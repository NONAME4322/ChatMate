import base64
import os
import threading
import time

import imutils
import numpy as np
import pyaudio
import pyautogui
from CTkMessagebox import CTkMessagebox

from ChatMate.client_side import client_utils
from ChatMate.client_side.meeting_page import meeting_page_functionality

import socket

from tkinter import *

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from cv2 import cv2

BUFF_SIZE = 65536


class MeetingClient:
    """
    Initializes the client object by prompting the user for their name,
    and setting various properties such as the host IP, TCP/UDP ports, buffer size,
    host UDP/TCP addresses, TCP/UDP socket objects, host name, client IP,
    and UDP socket options.
    """

    def __init__(self, meeting_page, meeting_tcp_address, meeting_udp_address, meeting_key):
        self.meeting_key = meeting_key
        self.cipher = AES.new(self.meeting_key, AES.MODE_ECB)

        self.stay_flag = True
        self.can_i_hear = True
        self.can_i_see = True
        self.meeting_page = meeting_page
        self.name = self.meeting_page.name
        self.senders = self.meeting_page.senders

        self.host_name = socket.gethostname()
        self.ip = socket.gethostbyname(self.host_name)

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.ip, 0))

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
        self.udp_socket.bind((self.ip, 0))
        self.udp_address = self.udp_socket.getsockname()

        self.meeting_tcp_address = meeting_tcp_address
        self.meeting_udp_address = meeting_udp_address

        self.tcp_socket.connect(self.meeting_tcp_address)
        self.tcp_send((self.name + str(self.udp_address)).encode())
        while self.tcp_recv() == b'there is already a user with that name':
            CTkMessagebox(title="invalid name", message="there is already a user with that name in the meeting",
                          icon="cancel").get()
            self.name = self.meeting_page.get_name_from_client()
            self.tcp_send(self.name.encode())

        self.py_audio = pyaudio.PyAudio()
        self.output_sound_stream = client_utils.output_sound_stream(self.py_audio)

        self.video_dict = {}
        self.screen_dict = {}

    def tcp_send(self, message):
        iv = os.urandom(16)

        # Encrypt the message using AES-CBC mode
        iv_cipher = AES.new(self.meeting_key, AES.MODE_CBC, iv)

        padded_message = pad(message, AES.block_size)
        encrypted_message = iv_cipher.encrypt(padded_message)

        # Combine the IV and encrypted message
        message_with_iv = iv + encrypted_message

        # Encrypt the entire message again using AES-ECB mode
        final_message = self.cipher.encrypt(message_with_iv)

        self.tcp_socket.send(final_message)

    def tcp_recv(self):
        encrypted_message = self.tcp_socket.recv(1024)

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

    def udp_send(self, data):
        self.udp_socket.sendto(data, self.meeting_udp_address)

    def udp_recv(self):
        return self.udp_socket.recv(BUFF_SIZE)

    def ask_screen_share(self):
        self.tcp_send(b'message to share screen')

    def ask_camera_share(self):
        self.tcp_send(b'message to share camera')

    def ask_microphone_share(self):
        self.tcp_send(b'message to share microphone')

    def close_camera(self):
        self.senders[self.name].set_camera(False)
        self.tcp_send(b'close camera')

    def close_screen(self):
        self.senders[self.name].set_screen(False)
        self.tcp_send(b'close screen')

    def close_microphone(self):
        self.senders[self.name].set_microphone(False)
        self.tcp_send(b'close microphone')

    def set_me_manager(self, my_name):
        for sender in self.senders.values():
            if sender.get_name() != my_name:
                sender.unlock_widgets()

    def remove_me_manager(self, my_name):
        for sender in self.senders.values():
            if sender.get_name() != my_name:
                sender.lock_widgets()

    def safe_window_destroy(self):
        for i in range(3):
            self.udp_send(b'q$q$q$q')
        if self.meeting_page.thread_counter == 0:
            self.meeting_page.root.destroy()
            self.tcp_socket.close()
            self.udp_socket.close()
        else:
            print(self.meeting_page.thread_counter, " threads are still running!")

    def tcp_listen(self):
        # in this function I am using a tcp socket to send and receive important commands
        # from the server such as close camera
        # I cant send the commands via udp because there is a risk that they
        # won't reach the destination
        self.senders[self.name].set_is_manager(client_utils.str_to_bool(self.tcp_recv().decode()))
        self.tcp_send(b'is host delivered')
        client_list = client_utils.str_to_list(self.tcp_recv().decode())
        for udp, name in zip(client_list[::2], client_list[1::2]):
            self.meeting_page.create_sender(udp, name)

        self.tcp_send(b'ready for properties')
        properties = self.tcp_recv()

        while properties != b'#':

            properties, property_to_apply = client_utils.split_packet(properties)

            if property_to_apply[0:7] == 'promote':
                name_to_promote = property_to_apply[8:]
                self.senders[name_to_promote].set_is_manager(True)

            elif property_to_apply[0:12] == 'block camera':
                name_to_block_camera = property_to_apply[13:]
                self.senders[name_to_block_camera].set_camera_blocked(True, self.senders[self.name].get_is_manager())

            elif property_to_apply[0:12] == 'block screen':
                name_to_block_screen = property_to_apply[13:]
                self.senders[name_to_block_screen].set_screen_blocked(True, self.senders[self.name].get_is_manager())

            elif property_to_apply[0:16] == 'block microphone':
                name_to_block_microphone = property_to_apply[17:]
                self.senders[name_to_block_microphone].set_microphone_blocked(True,
                                                                              self.senders[self.name].get_is_manager())

            elif property_to_apply[0:11] == 'open camera':
                name_to_open_camera = property_to_apply[12:]
                self.senders[name_to_open_camera].set_camera(True)

            elif property_to_apply[0:11] == 'open screen':
                name_to_open_screen = property_to_apply[12:]
                self.senders[name_to_open_screen].set_screen(True)

            elif property_to_apply[0:15] == 'open microphone':
                name_to_open_microphone = property_to_apply[16:]
                self.senders[name_to_open_microphone].set_microphone(True)

        if self.senders[self.name].get_is_manager():
            self.set_me_manager(self.name)
        else:
            self.remove_me_manager(self.name)

        udp_receive_thread = threading.Thread(target=self.udp_listen)
        udp_receive_thread.start()
        self.meeting_page.thread_counter += 1

        while self.stay_flag:
            packet = self.tcp_recv()
            if not packet:
                break
            if packet == b'you got kicked':
                self.stay_flag = not self.stay_flag
                CTkMessagebox(title="you got kicked", message="you got kicked").get()
                self.meeting_page.root.after(1000, self.safe_window_destroy)

            elif packet == b'you got promoted':
                CTkMessagebox(title="you got promoted", message="you are now a manager")
                self.senders[self.name].set_is_manager(True)
                self.set_me_manager(self.name)

            elif packet == b'you got degraded':
                CTkMessagebox(title="you got degraded", message="you are no longer a manager")
                self.senders[self.name].set_is_manager(False)
                self.remove_me_manager(self.name)

            elif packet[0:12] == b'chat message':
                message = packet[13:].decode()
                self.meeting_page.show_message(message)

            elif packet[0:7] == b'promote':
                name_to_promote = packet[8:].decode()
                self.senders[name_to_promote].set_is_manager(True)

            elif packet[0:7] == b'degrade':
                name_to_degrade = packet[8:].decode()
                self.senders[name_to_degrade].set_is_manager(False)

            elif packet[0:12] == b'block camera':
                name_to_block_camera = packet[13:].decode()
                if self.senders[name_to_block_camera].get_camera():
                    time.sleep(1)
                    self.senders[name_to_block_camera].set_camera(False)
                    client_utils.canvas_close_camera(self.senders[name_to_block_camera].get_canvas())
                self.senders[name_to_block_camera].set_camera_blocked(True, self.senders[self.name].get_is_manager())

            elif packet[0:12] == b'allow camera':
                name_to_allow_camera = packet[13:].decode()
                self.senders[name_to_allow_camera].set_camera_blocked(False, self.senders[self.name].get_is_manager())

            elif packet[0:12] == b'block screen':
                name_to_block_screen = packet[13:].decode()
                if self.senders[name_to_block_screen].get_screen():
                    time.sleep(1)
                    self.senders[name_to_block_screen].set_screen(False)
                    self.meeting_page.screen_camera_button.pack_forget()
                    if self.meeting_page.screen_frame.winfo_ismapped():
                        meeting_page_functionality.screen_camera_switch(self)
                self.senders[name_to_block_screen].set_screen_blocked(True, self.senders[self.name].get_is_manager())

            elif packet[0:12] == b'allow screen':
                name_to_allow_screen = packet[13:].decode()
                self.senders[name_to_allow_screen].set_screen_blocked(False, self.senders[self.name].get_is_manager())

            elif packet[0:16] == b'block microphone':
                name_to_block_microphone = packet[17:].decode()
                if self.senders[name_to_block_microphone].get_microphone():
                    time.sleep(1)
                    self.senders[name_to_block_microphone].set_microphone(False)
                self.senders[name_to_block_microphone].set_microphone_blocked(True,
                                                                              self.senders[self.name].get_is_manager())

            elif packet[0:16] == b'allow microphone':
                name_to_allow_microphone = packet[17:].decode()
                self.senders[name_to_allow_microphone].set_microphone_blocked(False,
                                                                              self.senders[self.name].get_is_manager())

            elif packet == b'the host blocked your camera':
                CTkMessagebox(title="blocked camera", message="the host blocked your camera")
                self.meeting_page.got_camera_blocked()

            elif packet == b'the host blocked your screen':
                CTkMessagebox(title="blocked screen", message="the host blocked your screen")
                self.meeting_page.got_screen_blocked()

            elif packet == b'the host blocked your microphone':
                CTkMessagebox(title="blocked microphone", message="the host blocked your microphone")
                self.meeting_page.got_microphone_blocked()

            elif packet == b'the host allowed your camera':
                CTkMessagebox(title="allowed camera", message="the host allowed your camera")
                self.senders[self.name].set_camera(False)

            elif packet == b'the host allowed your screen':
                CTkMessagebox(title="allowed screen", message="the host allowed your screen")
                self.senders[self.name].set_screen(False)

            elif packet == b'the host allowed your microphone':
                CTkMessagebox(title="allowed microphone", message="the host allowed your microphone")
                self.senders[self.name].set_microphone(False)

            elif packet == b'you can share screen':
                self.senders[self.name].set_screen(True)
                self.meeting_page.thread_counter += 1
                t_send = threading.Thread(target=self.send_screen)
                t_send.start()

            elif packet == b'you cannot share screen':
                self.meeting_page.on_off_screen.set("start screen sharing")
                CTkMessagebox(title="you cant share screen",
                              message="only 1 participate can share screen at a time or the host blocked your video")

            elif packet == b'you can share camera':
                self.senders[self.name].set_camera(True)
                self.meeting_page.thread_counter += 1
                t_send = threading.Thread(target=self.send_camera)
                t_send.start()

            elif packet == b'you cannot share camera':
                self.meeting_page.on_off_camera.set("start camera")
                CTkMessagebox(title="you cant share camera", message="the host blocked your camera")

            elif packet == b'you can share microphone':
                self.senders[self.name].set_microphone(True)
                self.meeting_page.thread_counter += 1
                t_send = threading.Thread(target=self.send_microphone)
                t_send.start()

            elif packet == b'you cannot share microphone':
                self.meeting_page.on_off_microphone.set("start microphone")
                CTkMessagebox(title="you cant share microphone", message="the host blocked your microphone")

            elif packet == b'the former host left so you are the new host':
                self.senders[self.name].set_is_manager(True)
                self.set_me_manager(self.name)

            else:
                packet, current_sender_name = client_utils.split_packet(packet)
                packet, packet_type = client_utils.split_packet(packet)
                if packet == b'new user connected: ':
                    current_sender_udp = packet_type
                    self.meeting_page.create_sender(current_sender_udp, current_sender_name)

                else:
                    packet, what_to_do = client_utils.split_packet(packet)
                    if what_to_do == "close":
                        if packet_type == "all":
                            time.sleep(1)
                            self.meeting_page.screen_camera_button.pack_forget()
                            if self.meeting_page.screen_frame.winfo_ismapped():
                                meeting_page_functionality.screen_camera_switch(self.meeting_page)
                            self.meeting_page.remove_sender_by_name(current_sender_name)

                        elif packet_type == "camera":
                            time.sleep(1)
                            self.senders[current_sender_name].set_camera(False)
                            client_utils.canvas_close_camera(self.senders[current_sender_name].get_canvas())

                        elif packet_type == 'screen':
                            time.sleep(1)
                            self.senders[current_sender_name].set_screen(False)
                            self.meeting_page.screen_camera_button.pack_forget()
                            if self.meeting_page.screen_frame.winfo_ismapped():
                                meeting_page_functionality.screen_camera_switch(self.meeting_page)
                            CTkMessagebox(title="screen sharing stopped",
                                          message=f"{current_sender_name} stopped screen sharing")

                        elif packet_type == 'microphone':
                            time.sleep(1)
                            self.senders[current_sender_name].set_microphone(False)
                    elif what_to_do == "open":
                        if packet_type == "camera":
                            self.senders[current_sender_name].set_camera(True)
                        elif packet_type == "screen":
                            self.meeting_page.screen_camera_button.pack(side=LEFT, padx=5)
                            self.senders[current_sender_name].set_screen(True)
                            CTkMessagebox(title="screen sharing started",
                                          message=f"{current_sender_name} started screen sharing")

                        elif packet_type == "microphone":
                            self.senders[current_sender_name].set_microphone(True)

        self.meeting_page.thread_counter -= 1

    # this function receives udp packets of video and audio and displays it
    # on the device
    def udp_listen(self):
        # Set the secret key
        key = self.meeting_key
        while self.stay_flag:
            packet = self.udp_recv()
            if packet != b'q$q$q$q':
                packet, current_name = client_utils.split_packet_without_decode(packet)
                current_name = self.cipher.decrypt(current_name)
                current_name = current_name[:-current_name[-1]]
                current_name = current_name.decode()
                packet, packet_type = client_utils.split_packet(packet)

                current_sender = self.senders[current_name]
                if packet_type == "camera":

                    if current_sender.get_allowed_camera():
                        threading.Thread(target=display_video_packet,
                                         args=(self, current_name, current_sender, packet, key, "camera")).start()

                elif packet_type == 'screen':
                    threading.Thread(target=display_video_packet,
                                     args=(self, current_name, current_sender, packet, key, "screen")).start()

                elif packet_type == "microphone":
                    if current_sender.get_allowed_microphone():
                        threading.Thread(target=display_audio_packet, args=(self, packet, key)).start()

        self.meeting_page.thread_counter -= 1

    # this function sends the camera stream from the sender to the receiver
    # through separate threads
    def send_camera(self):

        vid = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # webcam
        vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        frame_num = 1
        while self.stay_flag and self.senders[self.name].get_camera():
            _, frame = vid.read()
            frame = cv2.flip(frame, 1)
            frame = imutils.resize(frame, width=500)
            t_send_frame = threading.Thread(target=self.send_frame, args=(frame, frame_num, b'$SEP$camera'))
            t_send_frame.start()
            frame = imutils.resize(frame, height=int(self.senders[self.name].get_frame().winfo_height()))

            frame_num += 1
            photo = client_utils.photo_image(frame)
            self.senders[self.name].get_canvas().create_image(self.senders[self.name].get_frame().winfo_width() / 2,
                                                              self.senders[self.name].get_canvas().winfo_height() / 2,
                                                              image=photo)
            self.senders[self.name].get_canvas().image = photo
        client_utils.canvas_close_camera(self.senders[self.name].get_canvas())
        self.meeting_page.thread_counter -= 1

    # this function sends the current screen from the sender to the receiver
    # through separate threads
    def send_screen(self):
        frame_num = 1
        while self.stay_flag and self.senders[self.name].get_screen():
            # Take a screenshot of the screen
            screenshot = pyautogui.screenshot()
            # Convert the screenshot to a NumPy array
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            # frame = imutils.resize(frame, width=1200)
            t_send_frame = threading.Thread(target=self.send_frame, args=(frame, frame_num, b'$SEP$screen'))
            t_send_frame.start()
            frame_num += 1
        self.meeting_page.thread_counter -= 1

    # this function receive an opencv frame encrypt it and sends it via udp
    # if the frame size is too big to send with udp (over 65536 bytes)
    # the function will split the data and send it in parts
    def send_frame(self, frame, frame_num, packet_type):
        # Set the secret key
        key = self.meeting_key
        # Set the initialization vector
        iv = os.urandom(16)
        videoEncrypt = AES.new(key, AES.MODE_CBC, iv)
        encoded, message = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
        message = message.tobytes()
        # Determine the number of padding bytes needed
        padding_length = AES.block_size - (len(message) % AES.block_size)
        # Add the padding to the message
        message = message + (padding_length * chr(padding_length).encode())
        message = videoEncrypt.encrypt(message)
        encrypted_iv = self.cipher.encrypt(iv)
        # add the initialization vector to the message
        message = base64.b64encode(encrypted_iv + b'$SEP$' + message)
        num_of_cuts = message.__sizeof__() // 65000
        num_of_parts = num_of_cuts + 1
        len_of_cut = message.__len__() // num_of_parts

        part_num = 1

        while num_of_cuts > 0:
            to_send = message[:len_of_cut] + b'$SEP$' + str(part_num).encode() + b'$SEP$' + \
                      str(num_of_parts).encode() + b'$SEP$' + str(frame_num).encode() + packet_type
            self.udp_socket.sendto(to_send, self.meeting_udp_address)
            message = message[len_of_cut:]
            num_of_cuts -= 1
            part_num += 1
        self.udp_socket.sendto(message + b'$SEP$' + str(part_num).encode() + b'$SEP$' + \
                               str(num_of_parts).encode() + b'$SEP$' + str(frame_num).encode() + packet_type,
                               self.meeting_udp_address)
        frame_num += 1

    # this function sends the sound stream from the sender to the receiver
    def send_microphone(self):
        key = self.meeting_key
        input_sound_stream = client_utils.input_sound_stream(self.py_audio)
        while self.stay_flag and self.senders[self.name].get_microphone():
            data = input_sound_stream.read(3200)
            # encoding and encrypting process
            # Set the initialization vector
            iv = os.urandom(16)
            audioEncrypter = AES.new(key, AES.MODE_CBC, iv)
            # Determine the number of padding bytes needed
            padding_length = AES.block_size - (len(data) % AES.block_size)
            # Add the padding to the message
            data = data + (padding_length * chr(padding_length).encode())
            data = audioEncrypter.encrypt(data)
            encrypted_iv = self.cipher.encrypt(iv)
            # add the initialization vector to the message
            packet = base64.b64encode(encrypted_iv + b'$SEP$' + data)

            packet += b'$SEP$microphone'
            # size = 8569
            # encrypted size = 17111
            self.udp_send(packet)
        input_sound_stream.close()

        self.meeting_page.thread_counter -= 1

    def on_closing(self):

        msg = CTkMessagebox(title="Exit?", message="Do you want to close the program?",
                            icon="question", option_1="Cancel", option_2="Yes")
        if msg.get() == "Yes":
            self.stay_flag = not self.stay_flag
            self.tcp_send(b'message to quit')
            self.meeting_page.root.after(1000, self.safe_window_destroy)


def display_audio_packet(meeting_client, packet, key):
    decoded_message = base64.b64decode(packet)
    for i, letter in enumerate(decoded_message):
        if decoded_message[i:(i + 5)] == b'$SEP$':
            iv = meeting_client.cipher.decrypt(decoded_message[:i])
            decoded_message = decoded_message[i + 5:]
            decrypter = AES.new(key, AES.MODE_CBC, iv)
            decrypted_message = decrypter.decrypt(decoded_message)
            data = decrypted_message[:-decrypted_message[-1]]
            time.sleep(float(meeting_client.meeting_page.audio_delay_menu.get()))
            if meeting_client.can_i_hear:
                meeting_client.output_sound_stream.write(data)


def display_video_packet(meeting_client, current_name, current_sender, packet, key, camera_or_screen):
    packet, packet_num = client_utils.split_packet(packet)
    packet, num_of_parts = client_utils.split_packet(packet)
    num_of_parts = int(num_of_parts)
    packet, part_num = client_utils.split_packet(packet)
    part_num = int(part_num)

    if camera_or_screen == "camera":
        dictionary = meeting_client.video_dict
        current_tk_canvas = current_sender.get_canvas()
    else:
        dictionary = meeting_client.screen_dict
        current_tk_canvas = meeting_client.meeting_page.screen_canvas

    if current_name + " - " + packet_num not in dictionary.keys():
        dictionary[current_name + " - " + packet_num] = [''] * num_of_parts
    dictionary[current_name + " - " + packet_num][part_num - 1] = packet
    if '' not in dictionary[current_name + " - " + packet_num]:
        full_packet = b''
        for packet in dictionary[current_name + " - " + packet_num]:
            full_packet += packet
        try:
            # here we decode and decrypt the video packet
            decoded_message = base64.b64decode(full_packet)

            for i, letter in enumerate(decoded_message):
                if decoded_message[i:(i + 5)] == b'$SEP$':
                    iv = meeting_client.cipher.decrypt(decoded_message[:i])
                    decoded_message = decoded_message[i + 5:]
                    decrypter = AES.new(key, AES.MODE_CBC, iv)
                    decrypted_message = decrypter.decrypt(decoded_message)
                    data = decrypted_message[:-decrypted_message[-1]]
                    npdata = np.frombuffer(data, dtype=np.uint8)
                    frame = cv2.imdecode(npdata, 1)
                    frame = imutils.resize(frame, height=current_tk_canvas.winfo_height(),
                                           width=current_tk_canvas.winfo_width())
                    photo = client_utils.photo_image(frame)
                    time.sleep(float(meeting_client.meeting_page.video_delay_menu.get()))
                    if meeting_client.can_i_see:
                        current_tk_canvas.create_image(0, 0, image=photo, anchor=NW)
                        current_tk_canvas.image = photo
                    del dictionary[current_name + " - " + packet_num]
        except:
            pass
