from ChatMate.client_side.meeting_page.meeting_page_gui import MeetingPage
from ChatMate.client_side import client_utils

from CTkMessagebox import CTkMessagebox
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

import pyperclip



def create_meeting_callback(entry_page, popup, meeting_name, meeting_password):
    if not client_utils.is_alphanumeric(meeting_password) or not client_utils.is_alphanumeric(meeting_name):
        CTkMessagebox(title="Error", message="Meeting name and password can"
                                             " contain only english letters and numbers", icon="cancel")
    else:
        not_valid_or_address = entry_page.entry_client.create_meeting(meeting_name, meeting_password)
        if not_valid_or_address == "there is already a meeting with this name":
            CTkMessagebox(title="Error", message="There is already a meeting with this name", icon="cancel")
        elif not_valid_or_address == "there are too many meetings":
            CTkMessagebox(title="Error", message="there are too many meetings", icon="cancel")
        else:
            popup.destroy()

            meeting_tcp_address, meeting_udp_address = not_valid_or_address

            # Display a message box with the meeting name and password
            answer = CTkMessagebox(title="Meeting Info",
                                   message=f"You have created the following meeting:\n\n"
                                           f"Meeting Name: {meeting_name}\n"
                                           f"press OK to copy the meeting information (name and password) "
                                           f" to your clipboard").get()
            if answer == "OK":
                pyperclip.copy(f"Meeting Name: {meeting_name}  Meeting Password: {meeting_password}\n")
                CTkMessagebox(title="Copied",
                              message="Meeting information has been copied to your clipboard!").get()

            entry_page.close_page()

            meeting_key = key_from_password(meeting_password)
            MeetingPage(meeting_tcp_address, meeting_udp_address, meeting_key)


def join_meeting_callback(entry_page, popup, meeting_name, meeting_password):
    if not client_utils.is_alphanumeric(meeting_password) or not client_utils.is_alphanumeric(meeting_name):
        CTkMessagebox(title="Error", message="Meeting name and password can"
                                             " contain only english letters and numbers", icon="cancel")
    else:
        not_valid_or_address = entry_page.entry_client.is_valid_meeting(meeting_name, meeting_password)
        # Check if the meeting ID and password are not valid
        if not_valid_or_address == "no meeting":
            CTkMessagebox(title="Error", message="Invalid meeting ID or password", icon="cancel")
        elif not_valid_or_address == "too many clients":
            CTkMessagebox(title="Error", message="the limit of users in the limit has been reached", icon="cancel")

        else:
            popup.destroy()

            meeting_tcp_address, meeting_udp_address = not_valid_or_address

            # Display a message box with the meeting information
            answer = CTkMessagebox(title="Meeting Info",
                                   message=f"You have joined the following meeting:\n\n"
                                           f"Meeting Name: {meeting_name}\n"
                                           f"press OK to copy the meeting information (name and password)"
                                           f" to your clipboard").get()
            if answer == "OK":
                pyperclip.copy(f"Meeting Name: {meeting_name}  Meeting Password: {meeting_password}\n")
                CTkMessagebox(title="Copied",
                              message="Meeting information has been copied to your clipboard!").get()

            entry_page.close_page()

            meeting_key = key_from_password(meeting_password)
            MeetingPage(meeting_tcp_address, meeting_udp_address, meeting_key)


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
