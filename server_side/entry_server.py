from cryptography.hazmat.backends import default_backend
from meeting_server import MeetingServer
import server_utils

import socket
import threading
import multiprocessing

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EntryServer:

    def __init__(self, port):
        """
         Represents an entry server in a communication system.

         Attributes:
             host (str): The hostname of the server.
             port (int): The port number for accepting connections.
             socket (socket): The socket object for handling connections.
             meeting_servers (dict): A dictionary containing meeting information.
             private_key (rsa.RSAPrivateKey): The private key for encryption and decryption.
             public_key (rsa.RSAPublicKey): The public key corresponding to the private key.
             public_key_bytes (bytes): The serialized form of the public key.

         Methods:
             decrypt_message(encrypted_data: bytes) -> bytes:
                 Decrypts the given encrypted data using the private key of the server.

             encrypt_message(data: bytes, client_public_key: rsa.RSAPublicKey) -> bytes:
                 Encrypts the given data using the public key of a client.

             tcp_recv(connection: socket.socket) -> bytes:
                 Receives and decrypts a message from the specified connection.

             tcp_send(connection: socket.socket, message: bytes, connection_public_key: rsa.RSAPublicKey) -> None:
                 Encrypts the given message using the public key of a connection and sends it.

             start_listening() -> None:
                 Starts listening for incoming connections and handles them in separate threads.

             handle_connection(connection: socket.socket, address: Tuple[str, int]) -> None:
                 Handles a single connection from a client.

             key_from_password(password: str) -> bytes:
                 Derives a cryptographic key from the given password.

         """
        self.host = socket.gethostname()
        self.port = port
        # create a socket object
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # dictionary with a tuple of meeting name and password as key and correct server address as value
        self.meeting_servers = {}
        # Generate public and private keys
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,  # commonly used value
            key_size=2048  # size of the key in bits
        )
        self.public_key = self.private_key.public_key()
        self.public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)

    def decrypt_message(self, encrypted_data):
        decrypted_message = self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_message

    def encrypt_message(self, data, client_public_key):
        encrypted_data = client_public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_data

    def tcp_recv(self, connection):
        encrypted_message = connection.recv(1024)
        message = self.decrypt_message(encrypted_message)

        return message

    def tcp_send(self, connection, message, connection_public_key):
        encrypted_message = self.encrypt_message(message, connection_public_key)
        connection.send(encrypted_message)

    def start_listening(self):
        # bind the socket to a public host, and a port
        self.socket.bind((self.host, self.port))
        # become a server socket
        self.socket.listen()

        while True:
            # accept connections
            connection, address = self.socket.accept()
            connection_thread = threading.Thread(target=self.handle_connection, args=(connection, address))
            connection_thread.start()

    def handle_connection(self, connection, address):
        try:
            print(f"New connection from {address}")
            flag = True

            connection.send(self.public_key_bytes)
            connection_public_key = serialization.load_pem_public_key(connection.recv(1024), backend=default_backend())

            while flag:
                data = self.tcp_recv(connection)

                # Handle the data here
                if data[0:14] == b'create meeting':
                    if len(self.meeting_servers) >= 2:
                        self.tcp_send(connection, b'there are too many meetings',
                                      connection_public_key)
                    else:
                        data = data[15:]
                        meeting_name, meeting_password = server_utils.split_packet(data)
                        meeting_name = meeting_name.decode()
                        for meeting in self.meeting_servers.keys():
                            if meeting[0] == meeting_name:
                                self.tcp_send(connection, b'there is already a meeting with this name',
                                              connection_public_key)
                                break
                        else:
                            meeting_key = key_from_password(meeting_password)
                            meeting_password = hash(meeting_password)
                            print(f"new meeting has been made! meeting name: {meeting_name}")
                            parent_pipe, child_pipe = multiprocessing.Pipe()
                            meeting_server = multiprocessing.Process(target=MeetingServer,
                                                                     args=(child_pipe, meeting_key))
                            meeting_server.start()
                            meeting_server_tcp_address, meeting_server_udp_address = parent_pipe.recv()
                            parent_pipe.close()

                            self.meeting_servers[(meeting_name, meeting_password)] = [
                                meeting_server_tcp_address, meeting_server_udp_address, 1]
                            # 1 is the current number of users
                            self.tcp_send(connection, str(self.meeting_servers
                                                          [(meeting_name, meeting_password)][0:2]).encode(),
                                          connection_public_key)
                            flag = False
                            meeting_server.join()
                            self.meeting_servers.pop((meeting_name, meeting_password))

                elif data[0:12] == b'join meeting':
                    data = data[13:]
                    meeting_name, meeting_password = server_utils.split_packet(data)
                    meeting_name = meeting_name.decode()
                    meeting_password = hash(meeting_password)
                    if (meeting_name, meeting_password) in self.meeting_servers.keys():
                        if self.meeting_servers[(meeting_name, meeting_password)][2] < 3:
                            self.tcp_send(connection, str(self.meeting_servers
                                                          [(meeting_name, meeting_password)][0:2]).encode(),
                                          connection_public_key)
                            self.meeting_servers[(meeting_name, meeting_password)][2] += 1
                            flag = False
                        else:
                            self.tcp_send(connection, "the limit of users in the limit has been reached".encode(), connection_public_key)
                    else:
                        self.tcp_send(connection, "there is no such meeting".encode(), connection_public_key)
        except:
            print(f"{address} disconnected")


def key_from_password(password):
    # Convert password to bytes
    password_bytes = password.encode("utf-8")
    # Choose a salt value
    salt = b'salt value'
    # Choose the number of iterations for the PBKDF
    iterations = 100000
    # Choose the length of the key in bits (e.g., 128, 256)
    key_length = 128
    # Create the PBKDF object and generate the key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length // 8,
        salt=salt,
        iterations=iterations,
    )
    key = kdf.derive(password_bytes)
    return key


if __name__ == '__main__':
    server = EntryServer(9998)
    server.start_listening()
