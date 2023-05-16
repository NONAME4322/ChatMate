from ChatMate.client_side import client_utils

import socket

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

host_ip = socket.gethostbyname(socket.gethostname())
main_server_port = 9998


class EntryClient:

    def __init__(self):

        self.main_server_address = (host_ip, main_server_port)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host_name = socket.gethostname()
        self.ip = socket.gethostbyname(self.host_name)
        self.tcp_socket.bind((self.ip, 0))
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

    def encrypt_message(self, data):
        encrypted_data = self.server_public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_data

    def tcp_send(self, message):
        encrypted_message = self.encrypt_message(message)
        self.tcp_socket.send(encrypted_message)

    def tcp_recv(self):
        encrypted_message = self.tcp_socket.recv(1024)
        message = self.decrypt_message(encrypted_message)
        return message

    def start_connection(self):
        self.tcp_socket.connect(self.main_server_address)
        self.server_public_key = serialization.load_pem_public_key(self.tcp_socket.recv(1024),
                                                                   backend=default_backend())
        self.tcp_socket.send(self.public_key_bytes)

    def create_meeting(self, meeting_name, meeting_password):
        self.tcp_send(f"create meeting {meeting_name}$SEP${meeting_password}".encode())

        answer = self.tcp_recv()
        if answer == b'there is already a meeting with this name':
            return "there is already a meeting with this name"
        elif answer == b'there are too many meetings':
            return "there are too many meetings"
        else:
            meeting_tcp_address, meeting_udp_address = client_utils.two_address_str_to_two_tuples(answer.decode())
            return meeting_tcp_address, meeting_udp_address

    def is_valid_meeting(self, meeting_name, meeting_password):
        self.tcp_send(f"join meeting {meeting_name}$SEP${meeting_password}".encode())
        answer = self.tcp_recv()
        if answer == b'there is no such meeting':
            return "no meeting"
        elif answer == b'the limit of users in the limit has been reached':
            return "too many clients"
        else:
            meeting_tcp_address, meeting_udp_address = client_utils.two_address_str_to_two_tuples(answer.decode())
            return meeting_tcp_address, meeting_udp_address

    def close(self):
        self.tcp_socket.close()
