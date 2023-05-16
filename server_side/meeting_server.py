import os
import threading

import server_utils
import User

import select
import socket

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

BUFF_SIZE = 65536


class MeetingServer:
    """
      Class representing a meeting server.

      Attributes:
      - child_pipe: A pipe for communication with the child process.
      - meeting_key: The encryption key for the meeting.
      - cipher: An AES cipher object for encryption and decryption.
      - users: A list of User objects representing connected users.
      - share_screen_flag: A flag indicating if screen sharing is enabled.
      - stay_flag: A flag indicating if the server should continue running.
      - ip: The IP address of the server.
      - tcp_socket: A TCP socket for handling incoming connections.
      - tcp_port: The port number for the TCP socket.
      - tcp_address: The address (IP address, port) of the TCP socket.
      - udp_socket: A UDP socket for sending and receiving data.
      - udp_port: The port number for the UDP socket.
      - udp_address: The address (IP address, port) of the UDP socket.

      Methods:
      - __init__(self, child_pipe, meeting_key): Initializes the MeetingServer object.
      - tcp_send(self, connection, message): Sends an encrypted message over TCP to the specified connection.
      - tcp_recv(self, connection): Receives and decrypts a message from the specified connection.
      - socket_list(self): Returns a list of TCP sockets of all connected users.
      - udp_name_list(self): Returns a list of UDP addresses and names of all connected users.
      - disconnect_user(self, disconnecting_user): Disconnects a user from the server.
      - tcp_start_listening(self): all the tcp communication.
      - receive_and_send_to_all(self): all the udp communication.
      - process_packet(self, packet, client_address) the actual processing of the udp packets.
      """
    def __init__(self, child_pipe, meeting_key):
        self.child_pipe = child_pipe
        self.meeting_key = meeting_key
        self.cipher = AES.new(self.meeting_key, AES.MODE_ECB)

        self.users = []
        self.share_screen_flag = False
        self.stay_flag = True
        host = socket.gethostname()
        self.ip = socket.gethostbyname(host)

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to a public host, and a random unused port
        self.tcp_socket.bind((host, 0))
        self.tcp_port = self.tcp_socket.getsockname()[1]
        self.tcp_address = (self.ip, self.tcp_port)
        print('Tcp is at:', self.tcp_address)

        tcp_thread = threading.Thread(target=self.tcp_start_listening)
        tcp_thread.start()

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
        self.udp_socket.bind((host, 0))
        self.udp_port = self.udp_socket.getsockname()[1]
        self.udp_address = (self.ip, self.udp_port)
        print('Udp is at:', self.udp_address)

        udp_thread = threading.Thread(target=self.receive_and_send_to_all)
        udp_thread.start()

        child_pipe.send((self.tcp_address, self.udp_address))
        child_pipe.close()
        tcp_thread.join()
        udp_thread.join()

    def tcp_send(self, connection, message):
        iv = os.urandom(16)

        # Encrypt the message using AES-CBC mode
        iv_cipher = AES.new(self.meeting_key, AES.MODE_CBC, iv)

        padded_message = pad(message, AES.block_size)
        encrypted_message = iv_cipher.encrypt(padded_message)

        # Combine the IV and encrypted message
        message_with_iv = iv + encrypted_message

        # Encrypt the entire message again using AES-ECB mode
        final_message = self.cipher.encrypt(message_with_iv)

        connection.send(final_message)

    def tcp_recv(self, connection):
        encrypted_message = connection.recv(1024)

        # Decrypt the entire message using AES-ECB mode
        message_with_iv = self.cipher.decrypt(encrypted_message)

        # Separate the IV and encrypted message
        iv = message_with_iv[:16]
        encrypted_message = message_with_iv[16:]

        # Decrypt the message using AES-CBC mode
        iv_cipher = AES.new(self.meeting_key, AES.MODE_CBC, iv)
        padded_message = iv_cipher.decrypt(encrypted_message)
        message = unpad(padded_message, 16)
        return message

    def socket_list(self):
        socket_lst = []
        for user in self.users:
            socket_lst.append(user.get_tcp_socket())
        return socket_lst

    def udp_name_list(self):
        udp_name_lst = []
        for user in self.users:
            udp_name_lst.append(str(user.get_udp_address()))
            udp_name_lst.append(user.get_name())
        return udp_name_lst

    def disconnect_user(self, disconnecting_user):

        # sending a message to whoever got kicked, so it won't get stuck on recv
        self.tcp_send(disconnecting_user.get_tcp_socket(), b'q$q$q$q')
        self.udp_socket.sendto(b'q$q$q$q', disconnecting_user.get_udp_address())

        print(disconnecting_user, ' disconnected')
        self.users.remove(disconnecting_user)

        if disconnecting_user.get_is_manager():
            for user in self.users:
                if user.get_is_manager():
                    break
            else:
                if self.users.__len__() != 0:
                    self.users[0].set_is_manager(True)
                    self.tcp_send(self.users[0].get_tcp_socket(), b'the former host left so you are the new host')
                else:
                    self.stay_flag = False
                    print("no more clients")
                    print("meeting is over")

        if self.stay_flag:
            print("current client list:")
            print(*self.users, sep='\n')

        packet_all = b'close$SEP$all'
        packet_all += ('$SEP$' + disconnecting_user.get_name()).encode()
        for user in self.users:
            self.tcp_send(user.get_tcp_socket(), packet_all)
            self.udp_socket.sendto(b'q$q$q$q', user.get_udp_address())

    def tcp_start_listening(self):
        # become a server socket
        self.tcp_socket.listen()

        while self.stay_flag:
            sockets = self.socket_list()
            rlist, wlist, xlist = select.select([self.tcp_socket] + sockets, sockets, [], 1000)

            for current_socket in rlist:
                if current_socket is self.tcp_socket:
                    connection, user_address = current_socket.accept()
                    name_and_udp = self.tcp_recv(connection).decode()
                    udp_addr_str, user_name = server_utils.name_and_udp_split(name_and_udp)
                    while True:
                        for user in self.users:
                            if user.get_name() == user_name:
                                self.tcp_send(connection, b'there is already a user with that name')
                                user_name = self.tcp_recv(connection).decode()
                                break
                        else:
                            self.tcp_send(connection, b'name is okay')
                            break
                    udp_addr_tuple = server_utils.address_str_to_tuple(udp_addr_str)
                    user_list_to_send = str(self.udp_name_list()).encode()
                    print('GOT connection from ', user_address)
                    if self.users.__len__() == 0:
                        self.users.append(User.User(user_name, user_address, True, connection, udp_addr_tuple))
                        self.tcp_send(connection, b'True')
                    else:
                        self.users.append(User.User(user_name, user_address, False, connection, udp_addr_tuple))
                        self.tcp_send(connection, b'False')
                    self.tcp_recv(connection)
                    for user in self.users:
                        if user.get_tcp_socket() != connection:
                            self.tcp_send(user.get_tcp_socket(), ("new user connected: " + '$SEP$' + udp_addr_str +
                                                                  '$SEP$' + user_name).encode())

                        else:
                            self.tcp_send(user.get_tcp_socket(), user_list_to_send)

                    self.tcp_recv(connection)

                    properties_to_send = b'#'
                    for user in self.users:
                        if user.get_is_manager() and user.get_name() != user_name:
                            properties_to_send += (f'$SEP$promote {user.get_name()}'.encode())
                        if not user.get_allowed_camera():
                            properties_to_send += (f'$SEP$block camera {user.get_name()}'.encode())
                        if not user.get_allowed_screen():
                            properties_to_send += (f'$SEP$block screen {user.get_name()}'.encode())
                        if not user.get_allowed_microphone():
                            properties_to_send += (f'$SEP$block microphone {user.get_name()}'.encode())
                        if user.get_camera():
                            properties_to_send += (f'$SEP$open camera {user.get_name()}'.encode())
                        if user.get_screen():
                            properties_to_send += (f'$SEP$open screen {user.get_name()}'.encode())
                        if user.get_microphone():
                            properties_to_send += (f'$SEP$open microphone {user.get_name()}'.encode())

                    self.tcp_send(connection, properties_to_send)

                    print("current user list:")
                    print(*self.users, sep='\n')
                else:
                    packet = self.tcp_recv(current_socket)
                    current_user = self.users[0]
                    sending_user_name = ''
                    for user in self.users:
                        if user.get_tcp_socket() == current_socket:
                            current_user = user
                            sending_user_name = user.get_name()

                    if packet == b'message to share screen':
                        if (not self.share_screen_flag) and current_user.get_allowed_screen():
                            self.tcp_send(current_socket, b'you can share screen')
                            self.share_screen_flag = True
                            for user in self.users:
                                if user.get_tcp_socket() != current_socket:
                                    self.tcp_send(user.get_tcp_socket(),
                                                  f"open$SEP$screen$SEP${current_user.get_name()}".encode())
                                else:
                                    user.set_screen(True)
                        else:
                            self.tcp_send(current_socket, b'you cannot share screen')

                    elif packet == b'message to share camera':
                        if current_user.get_allowed_camera():
                            self.tcp_send(current_socket, b'you can share camera')
                            for user in self.users:
                                if user.get_tcp_socket() != current_socket:
                                    self.tcp_send(user.get_tcp_socket(),
                                                  f"open$SEP$camera$SEP${current_user.get_name()}".encode())
                                else:
                                    user.set_camera(True)
                        else:
                            self.tcp_send(current_socket, b'you cannot share camera')

                    elif packet == b'message to share microphone':
                        if current_user.get_allowed_microphone():
                            self.tcp_send(current_socket, b'you can share microphone')
                            for user in self.users:
                                if user.get_tcp_socket() != current_socket:
                                    self.tcp_send(user.get_tcp_socket(),
                                                  f"open$SEP$microphone$SEP${current_user.get_name()}".encode())
                                else:
                                    user.set_microphone(True)
                        else:
                            self.tcp_send(current_socket, b'you cannot share microphone')

                    elif packet == b'message to quit':
                        for disconnecting_user in self.users:
                            if disconnecting_user.get_tcp_socket() == current_socket:
                                self.disconnect_user(disconnecting_user)

                    elif packet == b'close camera':
                        for closing_user in self.users:
                            if closing_user.get_tcp_socket() == current_socket:
                                packet_camera = b'close$SEP$camera'
                                packet_camera += ('$SEP$' + closing_user.get_name()).encode()
                                for user in self.users:
                                    if user.get_tcp_socket() != current_socket:
                                        self.tcp_send(user.get_tcp_socket(), packet_camera)
                                        self.udp_socket.sendto(b'q$q$q$q', user.get_udp_address())
                                    else:
                                        user.set_camera(False)

                    elif packet == b'close screen':
                        self.share_screen_flag = False
                        for closing_user in self.users:
                            if closing_user.get_tcp_socket() == current_socket:
                                packet_screen = b'close$SEP$screen'
                                packet_screen += ('$SEP$' + closing_user.get_name()).encode()
                                for user in self.users:
                                    if user.get_tcp_socket() != current_socket:
                                        self.tcp_send(user.get_tcp_socket(), packet_screen)
                                        self.udp_socket.sendto(b'q$q$q$q', user.get_udp_address())
                                    else:
                                        user.set_screen(False)

                    elif packet == b'close microphone':
                        for closing_user in self.users:
                            if closing_user.get_tcp_socket() == current_socket:
                                packet_microphone = b'close$SEP$microphone'
                                packet_microphone += ('$SEP$' + closing_user.get_name()).encode()
                                for user in self.users:
                                    if user.get_tcp_socket() != current_socket:
                                        self.tcp_send(user.get_tcp_socket(), packet_microphone)
                                        self.udp_socket.sendto(b'q$q$q$q', user.get_udp_address())
                                    else:
                                        user.set_microphone(False)

                    elif packet[:12] == b'chat message':
                        message = f'chat message {sending_user_name}: {packet[13:].decode()}'.encode()
                        for user in self.users:
                            self.tcp_send(user.get_tcp_socket(), message)

                    elif packet[0:4] == b'kick':
                        name_to_kick = packet[5:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_kick:
                                self.tcp_send(user.get_tcp_socket(), b'you got kicked')
                                self.disconnect_user(user)

                    elif packet[0:12] == b'block camera':
                        name_to_block_camera = packet[13:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_block_camera:
                                self.tcp_send(user.get_tcp_socket(), b'the host blocked your camera')
                                user.set_allowed_camera(False)
                                user.set_camera(False)
                            else:
                                self.tcp_send(user.get_tcp_socket(), f'block camera {name_to_block_camera}'.encode())

                    elif packet[0:12] == b'allow camera':
                        name_to_allow_camera = packet[13:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_allow_camera:
                                self.tcp_send(user.get_tcp_socket(), b'the host allowed your camera')
                                user.set_allowed_camera(True)
                            else:
                                self.tcp_send(user.get_tcp_socket(), f'allow camera {name_to_allow_camera}'.encode())

                    elif packet[0:12] == b'block screen':
                        name_to_block_screen = packet[13:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_block_screen:
                                self.tcp_send(user.get_tcp_socket(), b'the host blocked your screen')
                                user.set_allowed_screen(False)
                                user.set_screen(False)

                            else:
                                self.tcp_send(user.get_tcp_socket(), f'block screen {name_to_block_screen}'.encode())

                    elif packet[0:12] == b'allow screen':
                        name_to_allow_screen = packet[13:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_allow_screen:
                                self.tcp_send(user.get_tcp_socket(), b'the host allowed your screen')
                                user.set_allowed_screen(True)
                            else:
                                self.tcp_send(user.get_tcp_socket(), f'allow screen {name_to_allow_screen}'.encode())

                    elif packet[0:16] == b'block microphone':
                        name_to_block_microphone = packet[17:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_block_microphone:
                                self.tcp_send(user.get_tcp_socket(), b'the host blocked your microphone')
                                user.set_allowed_microphone(False)
                                user.set_microphone(False)
                            else:
                                self.tcp_send(user.get_tcp_socket(),
                                              f'block microphone {name_to_block_microphone}'.encode())

                    elif packet[0:16] == b'allow microphone':
                        name_to_allow_microphone = packet[17:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_allow_microphone:
                                self.tcp_send(user.get_tcp_socket(), b'the host allowed your microphone')
                                user.set_allowed_microphone(True)
                            else:
                                self.tcp_send(user.get_tcp_socket(),
                                              f'allow microphone {name_to_allow_microphone}'.encode())

                    elif packet[0:7] == b'promote':
                        name_to_promote = packet[8:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_promote:
                                self.tcp_send(user.get_tcp_socket(), b'you got promoted')
                                user.set_is_manager(True)
                            else:
                                self.tcp_send(user.get_tcp_socket(), f'promote {name_to_promote}'.encode())

                    elif packet[0:7] == b'degrade':
                        name_to_degrade = packet[8:].decode()
                        for user in self.users:
                            if user.get_name() == name_to_degrade:
                                self.tcp_send(user.get_tcp_socket(), b'you got degraded')
                                user.set_is_manager(False)
                            else:
                                self.tcp_send(user.get_tcp_socket(), f'degrade {name_to_degrade}'.encode())
            if not rlist and len(self.users) == 0:
                self.stay_flag = False
                print("no more clients")
                print("meeting is over")
                break
            for socket_with_error in xlist:
                for user in self.users:
                    if user.get_tcp_socket() == socket_with_error:
                        self.disconnect_user(user)

    def receive_and_send_to_all(self):
        while self.stay_flag:
            if len(self.users) > 0:
                packet, client_address = self.udp_socket.recvfrom(65536)
                t_process_packet = threading.Thread(target=self.process_packet, args=(packet, client_address))
                t_process_packet.start()

    def process_packet(self, packet, client_address):
        is_client = False
        if packet != b'q$q$q$q':
            for user in self.users:
                if user.get_udp_address() == client_address:
                    padding_length = AES.block_size - (len(user.get_name().encode()) % AES.block_size)
                    # Add the padding to the message
                    padded_user_name = user.get_name().encode() + (padding_length * chr(padding_length).encode())
                    packet += (b'$SEP$' + self.cipher.encrypt(padded_user_name))
                    is_client = True
            if is_client:
                for user in self.users:
                    if user.get_udp_address() != client_address:
                        self.udp_socket.sendto(packet, user.get_udp_address())
