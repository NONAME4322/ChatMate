import datetime
import time

from CTkMessagebox import CTkMessagebox

from ChatMate.client_side.meeting_page.meeting_client import MeetingClient
from ChatMate.client_side.meeting_page import meeting_page_functionality
from ChatMate.client_side import client_utils
from ChatMate.client_side.meeting_page import Sender

from tkinter import *
import customtkinter as ctk

import threading


class MeetingPage:

    def __init__(self, meeting_tcp_address, meeting_udp_address, meeting_key):

        self.root = ctk.CTk()

        self.name = self.get_name_from_client()

        if self.name is not False:
            self.senders = {}
            self.last_refresh_senders = list(self.senders.values())

            self.meeting_client = MeetingClient(self, meeting_tcp_address, meeting_udp_address, meeting_key)
            self.name = self.meeting_client.name

            self.root.geometry(f"800x450")

            # Make the window resizable
            self.root.resizable(True, True)

            # Create a frame for all the widgets
            self.main_frame = ctk.CTkFrame(self.root, fg_color=("gray95", "gray10"))
            self.main_frame.pack(fill="both", expand=True)
            self.main_frame.bind("<Configure>", lambda event: threading.Thread(target=self.refresh_videos).start())

            self.buttons_frame = ctk.CTkFrame(self.main_frame, height=40)
            self.buttons_frame.pack(side=TOP, pady=5)

            self.frame_for_pictures = ctk.CTkFrame(self.main_frame, fg_color=("gray95", "gray10"))
            self.frame_for_pictures.pack()
            self.frame_for_pictures.place(relx=0.5, rely=0.52, anchor='center')

            self.screen_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray95", "gray10"))
            self.screen_canvas = Canvas(self.screen_frame, highlightbackground="black")
            self.screen_canvas.pack()
            self.user_data_frame = ctk.CTkFrame(self.main_frame)
            self.chat_frame = ctk.CTkFrame(self.main_frame)
            self.messages_frame = ctk.CTkScrollableFrame(self.chat_frame, width=200, height=300)
            self.messages_frame.columnconfigure(0, weight=2)
            self.messages_frame.columnconfigure(1, weight=1)
            self.messages_frame.pack(expand=True, fill="both", padx=5, pady=5)

            self.on_off_camera = StringVar()
            self.on_off_screen = StringVar()
            self.on_off_microphone = StringVar()
            self.screen_or_camera = StringVar()

            self.create_widgets()
            self.create_sender(("127.0.0.1", 22222), self.name)
            self.senders[self.name].lock_my_widgets()

            self.thread_counter = 0

            tcp_thread = threading.Thread(target=self.meeting_client.tcp_listen)
            tcp_thread.start()
            self.thread_counter += 1

            self.root.protocol("WM_DELETE_WINDOW", self.meeting_client.on_closing)
            self.root.mainloop()

    def get_name_from_client(self):
        name = ""
        # get the name from the client
        while True:
            name_dialog = ctk.CTkInputDialog(text="Enter what you want to be "
                                                  "called in the meeting:", title="Meeting Name")
            name = name_dialog.get_input()
            if name is None:
                msg = CTkMessagebox(title="Exit?", message="Do you want to close the program?",
                                    icon="question", option_1="Cancel", option_2="Yes")
                if msg.get() == "Yes":
                    self.root.destroy()
                    return False
            else:
                if not client_utils.is_alphanumeric(name):
                    CTkMessagebox(title="invalid name", message="name can contain only english letters and numbers",
                                  icon="cancel").get()
                else:
                    return name

    def create_widgets(self):
        view_or_hide = StringVar()
        view_or_hide.set("view users")
        btn_users = ctk.CTkButton(self.buttons_frame,
                                  textvariable=view_or_hide,
                                  text_color='#202020',
                                  width=0,
                                  command=lambda: meeting_page_functionality.view_hide_users(self.user_data_frame,
                                                                                             view_or_hide))
        btn_users.pack(side=LEFT, padx=5)

        # Create all the buttons on the top
        # Create a StringVar to track the state of the button
        self.on_off_camera.set("start camera")
        btn_camera = ctk.CTkButton(self.buttons_frame,
                                   textvariable=self.on_off_camera,
                                   text_color='#202020',
                                   width=0,
                                   command=lambda: meeting_page_functionality.start_stop_camera(self.meeting_client,
                                                                                                self.on_off_camera))
        btn_camera.pack(side=LEFT, padx=5)

        self.on_off_microphone.set("start microphone")
        btn_microphone = ctk.CTkButton(self.buttons_frame,
                                       textvariable=self.on_off_microphone,
                                       text_color='#202020',
                                       width=0,
                                       command=lambda: meeting_page_functionality.start_stop_microphone(
                                           self.meeting_client,
                                           self.on_off_microphone))

        btn_microphone.pack(side=LEFT, padx=5)

        self.on_off_screen.set("start screen sharing")
        btn_screen = ctk.CTkButton(self.buttons_frame,
                                   textvariable=self.on_off_screen,
                                   text_color='#202020',
                                   width=0,
                                   command=lambda: meeting_page_functionality.start_stop_screen(self.meeting_client,
                                                                                                self.on_off_screen))

        btn_screen.pack(side=LEFT, padx=5)

        self.screen_or_camera.set("press to watch share screen")
        self.screen_camera_button = ctk.CTkButton(self.buttons_frame,
                                                  textvariable=self.screen_or_camera,
                                                  text_color='#202020',
                                                  width=0,
                                                  command=lambda: meeting_page_functionality.screen_camera_switch(self))

        open_or_close = StringVar()
        open_or_close.set("open chat")
        btn_chat = ctk.CTkButton(self.buttons_frame,
                                 textvariable=open_or_close,
                                 text_color='#202020',
                                 width=0,
                                 command=lambda: meeting_page_functionality.open_close_chat(self.chat_frame,
                                                                                            open_or_close))

        btn_chat.pack(side=RIGHT, padx=5)

        self.chat_entry = ctk.CTkEntry(self.chat_frame, width=170, placeholder_text="Type message here")
        self.chat_entry.pack(side=LEFT, padx=5, pady=5)

        chat_send_btn = ctk.CTkButton(self.chat_frame, text="send",
                                      text_color='#202020', width=30,
                                      command=lambda: meeting_page_functionality.send_message(self.chat_entry,
                                                                                              self.meeting_client))
        chat_send_btn.pack(side=RIGHT, padx=5, pady=5)

        video_delay_label = ctk.CTkLabel(self.user_data_frame, text="Video delay")
        video_delay_label.grid(row=0, column=0, padx=5, columnspan=2)

        self.video_delay_menu = ctk.CTkOptionMenu(self.user_data_frame,
                                                  values=["0.0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8",
                                                          "0.9", "1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7",
                                                          "1.8", "1.9", "2.0"],
                                                  command=lambda choice: meeting_page_functionality.pause_video
                                                  (self.root, self.meeting_client, 2000))

        self.video_delay_menu.grid(row=0, column=2, padx=5, columnspan=3)

        audio_delay_label = ctk.CTkLabel(self.user_data_frame, text="Audio delay")
        audio_delay_label.grid(row=1, column=0, padx=5, columnspan=2)

        self.audio_delay_menu = ctk.CTkOptionMenu(self.user_data_frame,
                                                  values=["0.0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8",
                                                          "0.9", "1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6",
                                                          "1.7", "1.8", "1.9", "2.0"],
                                                  command=lambda choice: meeting_page_functionality.pause_audio
                                                  (self.root, self.meeting_client, 2000))
        self.audio_delay_menu.grid(row=1, column=2, padx=5, columnspan=3)

        # Create the user data frame

        # Create a label widget for the "Name" column
        name_label = ctk.CTkLabel(self.user_data_frame, text="Name")
        name_label.grid(row=2, column=0, padx=5)

        # Create a label widget for the "Manager" column
        manager_label = ctk.CTkLabel(self.user_data_frame, text="Manager")
        manager_label.grid(row=2, column=1, padx=5)

        # Create a label widget for the "Video" column
        camera_label = ctk.CTkLabel(self.user_data_frame, text="Camera")
        camera_label.grid(row=2, column=2, padx=5)

        # Create a label widget for the "Microphone" column
        microphone_label = ctk.CTkLabel(self.user_data_frame, text="Microphone")
        microphone_label.grid(row=2, column=3, padx=5)

        # Create a label widget for the "Share Screen" column
        share_screen_label = ctk.CTkLabel(self.user_data_frame, text="Share Screen")
        share_screen_label.grid(row=2, column=4, padx=5)

    def create_sender(self, udp_addr, name):

        # get the number of rows and columns in the grid
        columns, rows = self.user_data_frame.grid_size()

        name_label = ctk.CTkLabel(self.user_data_frame, text=name)
        name_label.grid(row=rows, column=0, padx=5, pady=5)
        is_manager_var = ctk.Variable(value=False)
        is_manager_switch = ctk.CTkSwitch(self.user_data_frame, variable=is_manager_var, text="", width=0,
                                          command=lambda: meeting_page_functionality.promote_or_degrade(
                                              self.meeting_client, is_manager_var, name))
        is_manager_switch.grid(row=rows, column=1, padx=5, pady=5)

        kick_btn = ctk.CTkButton(self.user_data_frame, text="kick", width=10,
                                 command=lambda: self.meeting_client.tcp_send(("kick " + name).encode()))

        if self.senders != {}:
            if self.senders[self.name].get_is_manager():
                values = ["hide", "block"]
                screen_values = ["block"]
                kick_btn.grid(row=rows, column=5, padx=5, pady=5)
            else:
                is_manager_switch.configure(state='disabled')
                values = ["hide"]
                screen_values = []
        else:
            values = ["hide"]
            screen_values = []

        camera_var = ctk.StringVar(value="closed")
        camera_option_menu = ctk.CTkOptionMenu(self.user_data_frame,
                                               values=values,
                                               variable=camera_var,
                                               command=lambda event: meeting_page_functionality.camera_commands
                                               (self.meeting_client, camera_option_menu, camera_var, name),
                                               width=10)
        camera_option_menu.grid(row=rows, column=2, padx=5, pady=5)

        microphone_var = ctk.StringVar(value="closed")

        microphone_option_menu = ctk.CTkOptionMenu(self.user_data_frame,
                                                   values=values,
                                                   variable=microphone_var,
                                                   command=lambda event: meeting_page_functionality.microphone_commands
                                                   (self.meeting_client, microphone_option_menu, microphone_var, name),
                                                   width=10)
        microphone_option_menu.grid(row=rows, column=3, padx=5, pady=5)

        screen_var = ctk.StringVar(value="closed")
        screen_option_menu = ctk.CTkOptionMenu(self.user_data_frame,
                                               values=screen_values,
                                               variable=screen_var,
                                               command=lambda event: meeting_page_functionality.screen_commands
                                               (self.meeting_client, screen_option_menu, screen_var, name),
                                               width=10)
        screen_option_menu.grid(row=rows, column=4, padx=5, pady=5)

        frame_for_canvas = ctk.CTkFrame(self.frame_for_pictures)
        canvas = ctk.CTkCanvas(frame_for_canvas, highlightbackground="black")
        canvas.pack()
        name_label2 = ctk.CTkLabel(frame_for_canvas, text=name)
        client_utils.canvas_close_camera(canvas)
        canvas.create_window(0, 0, window=name_label2, anchor=NW)
        new_sender = Sender.Sender(udp_addr, name, name_label, is_manager_switch, is_manager_var, camera_option_menu,
                                   microphone_option_menu, screen_option_menu, kick_btn, frame_for_canvas, canvas)
        self.senders[name] = new_sender
        threading.Thread(target=self.refresh_videos).start()

    # this function is always refresh the layout of the videos on the screen to fit inside the window
    def refresh_videos(self):

        # I am using a copy of the senders dict because if a sender left mid-iteration of the loop it causes an error
        current_senders = list(self.senders.values())
        self.main_frame.update()
        num_of_senders = current_senders.__len__()
        # determining the height of the share screen canvas
        share_height = min(self.main_frame.winfo_width(),
                           int(self.main_frame.winfo_height()
                               * 16 / 9)) / 16 * 9 - self.buttons_frame.winfo_height() * 2
        # updating the share screen canvas
        self.screen_canvas.configure(width=share_height * 16 / 9, height=share_height)
        # this function returns the size of each video and how to arrange the video on a table optimally
        width, columns, rows = client_utils.optimal_layout(self.main_frame.winfo_width(),
                                                           self.main_frame.winfo_height(), num_of_senders,
                                                           self.buttons_frame.winfo_height())
        # number of empty spaces in the grid
        empty_spaces = rows * columns - num_of_senders
        # counter to check we are not passing the number of users in the loop
        counter = 0
        # the loop grid the users on the correct spots on the grid
        for row_num in range(rows):
            # if we are on the last row and there are empty spaces we need to grid the videos in the middle
            if row_num == (rows - 1):
                for column_num in range(columns):
                    if counter < num_of_senders:
                        if empty_spaces % 2 == 0:
                            current_senders[counter].get_frame().grid(row=row_num + 1,
                                                                      column=column_num + (empty_spaces // 2),
                                                                      columnspan=1,
                                                                      padx=5, pady=5)
                            current_senders[counter].get_canvas().configure(width=(width - 8),
                                                                            height=((width - 8) * 9 / 16) - 4)
                        else:
                            current_senders[counter].get_frame().grid(row=row_num + 1,
                                                                      column=column_num + (empty_spaces // 2),
                                                                      columnspan=2,
                                                                      padx=5, pady=5)
                            current_senders[counter].get_canvas().configure(width=(width - 8),
                                                                            height=((width - 8) * 9 / 16) - 4)

                        counter += 1
            # if im not on the last row
            else:
                for column_num in range(columns):
                    if counter < num_of_senders:
                        current_senders[counter].get_frame().grid(row=row_num + 1, column=column_num, padx=5, pady=5)
                        current_senders[counter].get_canvas().configure(width=(width - 8),
                                                                        height=((width - 8) * 9 / 16) - 4)
                    counter += 1

        for last_refresh_sender in self.last_refresh_senders:
            if last_refresh_sender not in current_senders:
                last_refresh_sender.get_frame().destroy()
        self.last_refresh_senders = current_senders

    def got_camera_blocked(self):
        if self.senders[self.name].get_camera():
            self.on_off_camera.set("start camera")
            self.senders[self.name].set_camera(False)
            client_utils.canvas_close_camera(self.senders[self.name].get_canvas())
        self.senders[self.name].get_camera_option_menu().set("blocked")

    def got_screen_blocked(self):
        if self.senders[self.name].get_screen():
            self.on_off_screen.set("start screen sharing")
            self.senders[self.name].set_screen(False)
            self.screen_camera_button.pack_forget()
            if self.screen_frame.winfo_ismapped():
                meeting_page_functionality.screen_camera_switch(self)
        self.senders[self.name].get_screen_option_menu().set("blocked")

    def got_microphone_blocked(self):
        if self.senders[self.name].get_microphone():
            self.on_off_microphone.set("start microphone")
            self.senders[self.name].set_microphone(False)
        self.senders[self.name].get_microphone_option_menu().set("blocked")

    def remove_sender_by_name(self, name):

        self.senders[name].remove_from_commands()
        time.sleep(0.2)
        self.senders.pop(name)
        self.refresh_videos()

    def show_message(self, message):
        _, rows = self.messages_frame.grid_size()

        message_label = ctk.CTkLabel(self.messages_frame, text=message)
        message_label.grid(row=rows, column=0, sticky='w')
        current_time = datetime.datetime.now()
        time_label = ctk.CTkLabel(self.messages_frame, text=current_time.strftime("%H:%M"))
        time_label.grid(row=rows, column=1, sticky='e')
