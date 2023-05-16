

from ChatMate.client_side import client_utils


def view_hide_users(user_data_frame, view_or_hide):
    """ This function toggles the visibility of the user data frame based on the value of the view_or_hide variable.
     If view_or_hide is set to "view users,
    " the user data frame is displayed. Otherwise, if it is set to "hide users," the user data frame is hidden."""
    if view_or_hide.get() == "view users":
        view_or_hide.set("hide users")
        user_data_frame.place(x=0, y=50)
    else:
        view_or_hide.set("view users")
        user_data_frame.place_forget()


def camera_commands(meeting_client, camera_menu, camera_var, name):
    """This function handles different camera commands based on the selected value of camera_var.
     It performs actions such as blocking/unblocking the camera,
     hiding/showing the camera feed, and updating the camera menu options accordingly."""
    if camera_var.get() == "block":
        meeting_client.tcp_send(("block camera " + name).encode())
        camera_var.set("blocked")
        camera_menu.configure(values=["unblock"])

    elif camera_var.get() == "unblock":
        meeting_client.tcp_send(("allow camera " + name).encode())
        camera_menu.configure(values=["hide", "block"])

    elif camera_var.get() == "hide":
        camera_var.set("hidden")
        camera_menu.configure(values=["show"])
        meeting_client.senders[name].set_allowed_camera(False)
        client_utils.canvas_close_camera(meeting_client.senders[name].get_canvas())

    elif camera_var.get() == "show":
        meeting_client.senders[name].set_allowed_camera(True)
        if meeting_client.senders[name].get_camera():
            camera_var.set("open")
        else:
            camera_var.set("closed")

        if meeting_client.senders[meeting_client.name].get_is_manager():
            camera_menu.configure(values=["hide", "block"])
        else:
            camera_menu.configure(values=["hide"])


def microphone_commands(meeting_client, microphone_menu, microphone_var, name):
    """This function handles different microphone commands based on the selected value of microphone_var.
     It performs actions such as blocking/unblocking the microphone,
     hiding/showing the microphone status, and updating the microphone menu options accordingly."""
    if microphone_var.get() == "block":
        meeting_client.tcp_send(("block microphone " + name).encode())
        microphone_var.set("blocked")
        microphone_menu.configure(values=["unblock"])

    elif microphone_var.get() == "unblock":
        meeting_client.tcp_send(("allow microphone " + name).encode())
        microphone_var.set("")
        microphone_menu.configure(values=["hide", "block"])

    elif microphone_var.get() == "hide":
        microphone_var.set("hidden")
        microphone_menu.configure(values=["show"])
        meeting_client.senders[name].set_allowed_microphone(False)

    elif microphone_var.get() == "show":
        meeting_client.senders[name].set_allowed_microphone(True)
        if meeting_client.senders[name].get_microphone():
            microphone_var.set("open")
        else:
            microphone_var.set("closed")
        if meeting_client.senders[meeting_client.name].get_is_manager():
            microphone_menu.configure(values=["hide", "block"])
        else:
            microphone_menu.configure(values=["hide"])


def screen_commands(meeting_client, screen_menu, screen_var, name):
    """This function handles different screen sharing commands based on the selected value of screen_var.
     It performs actions such as blocking/unblocking the screen sharing,
     hiding/showing the screen sharing status, and updating the screen menu options accordingly."""
    if screen_var.get() == "block":
        meeting_client.tcp_send(("block screen " + name).encode())
        screen_var.set("blocked")
        screen_menu.configure(values=["unblock"])

    elif screen_var.get() == "unblock":
        meeting_client.tcp_send(("allow screen " + name).encode())
        screen_var.set("")
        screen_menu.configure(values=["hide", "block"])


def promote_or_degrade(meeting_client, is_manager_var, name):
    """This function handles promoting or degrading a user's role based on the value of is_manager_var. If
    is_manager_var is true, the user is promoted to a manager. Otherwise, the user is degraded to a regular participant.
    """
    if is_manager_var.get():
        meeting_client.tcp_send(("promote " + name).encode())
    else:
        meeting_client.tcp_send(("degrade " + name).encode())


def start_stop_camera(meeting_client, on_off_camera):
    """

This function handles starting or stopping the camera feed based on the value of on_off_camera.
 If on_off_camera is set to "start camera",
  the camera feed is started. Otherwise, if it is set to "stop camera," the camera feed is stopped.
    """
    if on_off_camera.get() == "start camera":
        on_off_camera.set("stop camera")
        meeting_client.ask_camera_share()
    else:
        on_off_camera.set("start camera")
        meeting_client.close_camera()


def start_stop_screen(meeting_client, on_off_screen):
    """This function handles starting or stopping screen sharing based on the value of on_off_screen.
     If on_off_screen is set to "start screen sharing,"
     screen sharing is started. Otherwise, if it is set to "stop screen sharing," screen sharing is stopped."""
    if on_off_screen.get() == "start screen sharing":
        on_off_screen.set("stop screen sharing")
        meeting_client.ask_screen_share()
    else:
        on_off_screen.set("start screen sharing")
        meeting_client.close_screen()


def start_stop_microphone(meeting_client, on_off_microphone):
    """
This function handles starting or stopping microphone sharing based on the value of on_off_microphone.
 If on_off_microphone is set to "start microphone,"
 microphone sharing is started. Otherwise, if it is set to "stop microphone," microphone sharing is stopped.
    """
    if on_off_microphone.get() == "start microphone":
        on_off_microphone.set("stop microphone")
        meeting_client.ask_microphone_share()
    else:
        on_off_microphone.set("start microphone")
        meeting_client.close_microphone()


def open_close_chat(chat_frame, open_or_close):
    """
    This function toggles the visibility of the chat frame based on the value of open_or_close.
     If open_or_close is set to "open chat," the chat frame is displayed.
    Otherwise, if it is set to "close chat," the chat frame is hidden.
    """
    if open_or_close.get() == "open chat":
        open_or_close.set("close chat")
        chat_frame.place(relx=1.0, y=50, anchor='ne')
    else:
        open_or_close.set("open chat")
        chat_frame.place_forget()


def screen_camera_switch(meeting_page):
    """
    This function switches between viewing the shared screen and viewing the camera feeds on the meeting page.
     It adjusts the visibility of the screen frame and the frame for pictures accordingly.
    """
    if meeting_page.screen_or_camera.get() == "press to watch share screen":
        meeting_page.frame_for_pictures.place_forget()
        meeting_page.screen_frame.pack()
        meeting_page.screen_or_camera.set("press to watch cameras")
    else:
        meeting_page.screen_frame.pack_forget()
        meeting_page.frame_for_pictures.place(relx=0.5, rely=0.52, anchor='center')
        meeting_page.screen_or_camera.set("press to watch share screen")


def pause_video(root, meeting_client, how_long):
    """
    This function pauses the video feed from the meeting client for a specified duration
    (how_long in milliseconds) by setting
    meeting_client.can_i_see to False. After the specified duration, it sets meeting_client.can_i_see back to True.
    """
    meeting_client.can_i_see = False

    root.after(how_long, lambda: set_true(meeting_client))

    def set_true(meeting_client):
        meeting_client.can_i_see = True


def pause_audio(root, meeting_client, how_long):
    """
    This function pauses the audio feed
    from the meeting client for a specified duration (how_long in milliseconds)
     by setting meeting_client.can_i_hear to False.
     After the specified duration, it sets meeting_client.can_i_hear back to True.
    """
    meeting_client.can_i_hear = False

    root.after(how_long, lambda: set_true(meeting_client))

    def set_true(meeting_client):
        meeting_client.can_i_hear = True


def send_message(entry, meeting_client):
    """

    This function sends a chat message from the meeting
    client by encoding and sending the message text via TCP using meeting_client.tcp_send().
     It then clears the text entry widget (entry) after sending the message.
    """
    meeting_client.tcp_send(f'chat message {entry.get()}'.encode())
    entry.delete(0, 100)
