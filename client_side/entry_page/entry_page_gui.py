import os

from ChatMate.client_side.entry_page.entry_client import EntryClient
from ChatMate.client_side.entry_page import entry_page_functionality

from tkinter import *
from PIL import Image
import customtkinter as ctk


class EntryPage:

    def __init__(self, root):
        # Set the size of the window to around 6/10 of the screen size
        self.root = root

        self.root.geometry(f"800x450")

        # Make the window non-resizable
        self.root.resizable(False, False)

        # Create a frame for the logo and buttons
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.entry_client = EntryClient()
        self.entry_client.start_connection()

    def create_widgets(self):
        logo_image = ctk.CTkImage(Image.open(os.path.join(os.getcwd(),
                                                          'ChatMate\\client_side\\logo.png')),
                                  size=(400, 200))

        # Add a label for the logo image
        logo_label = ctk.CTkLabel(self.main_frame, image=logo_image, text="")
        logo_label.pack(pady=20)

        # Create a frame for the buttons
        button_frame = ctk.CTkFrame(self.main_frame, height=100)
        button_frame.pack(fill="both", expand=True)

        my_font = ctk.CTkFont(size=30)

        # Create the "Create Meeting" button
        create_button = ctk.CTkButton(master=button_frame,
                                      width=300,
                                      height=150,
                                      corner_radius=15,
                                      text="Create Meeting",
                                      font=my_font,
                                      text_color='#202020',
                                      command=lambda: self.create_meeting())

        create_button.pack(side=LEFT, padx=50)

        # Create the "Join Meeting" button
        join_button = ctk.CTkButton(master=button_frame,
                                    width=300,
                                    height=150,
                                    corner_radius=15,
                                    text="Join Meeting",
                                    font=my_font,
                                    text_color='#202020',
                                    command=lambda: self.join_meeting())

        join_button.pack(side=RIGHT, padx=50)

    # Create the "Join Meeting" button
    def join_meeting(self):
        popup = ctk.CTkToplevel(self.main_frame)
        popup.title("Join Meeting")
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        popup.geometry("+%d+%d" % (x + 560, y + 60))
        popup.geometry("300x200")
        popup.resizable(False, False)

        popup.wm_transient(self.main_frame)

        empty_label = ctk.CTkLabel(popup, text="")
        empty_label.pack()

        meeting_name_entry = ctk.CTkEntry(popup,
                                          placeholder_text="Meeting Name",
                                          width=200,
                                          height=30,
                                          border_width=2,
                                          corner_radius=10)
        meeting_name_entry.pack(pady=5)

        meeting_password_entry = ctk.CTkEntry(popup,
                                              placeholder_text="Meeting Password",
                                              width=200,
                                              height=30,
                                              border_width=2,
                                              corner_radius=10,
                                              show="\u2022")
        meeting_password_entry.pack(pady=5)

        join_button = ctk.CTkButton(master=popup,
                                    width=200,
                                    height=40,
                                    corner_radius=10,
                                    text_color='#202020',
                                    text="Join Meeting",
                                    command=lambda: entry_page_functionality.join_meeting_callback(self, popup,
                                                                                                   meeting_name_entry.get(),
                                                                                                   meeting_password_entry.get()))

        join_button.pack(pady=10)

    # Create the "Join Meeting" button
    def create_meeting(self):
        popup = ctk.CTkToplevel(self.main_frame)
        popup.title("Create Meeting")
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        popup.geometry("+%d+%d" % (x + 65, y + 60))
        popup.geometry("300x200")
        popup.resizable(False, False)
        popup.wm_transient(self.main_frame)
        empty_label = ctk.CTkLabel(popup, text="")
        empty_label.pack()

        meeting_name_entry = ctk.CTkEntry(popup,
                                          placeholder_text="Meeting Name",
                                          width=200,
                                          height=30,
                                          border_width=2,
                                          corner_radius=10)
        meeting_name_entry.pack(pady=5)
        meeting_password_entry = ctk.CTkEntry(popup,
                                              placeholder_text="Meeting Password",
                                              width=200,
                                              height=30,
                                              border_width=2,
                                              corner_radius=10,
                                              show="\u2022")
        meeting_password_entry.pack(pady=5)

        create_button = ctk.CTkButton(master=popup,
                                      width=200,
                                      height=40,
                                      corner_radius=10,
                                      text_color='#202020',
                                      text="Create Meeting",
                                      command=lambda: entry_page_functionality.create_meeting_callback(self, popup,
                                                                                                       meeting_name_entry.get(),
                                                                                                       meeting_password_entry.get()))

        create_button.pack(pady=10)

    def close_page(self):
        self.entry_client.close()
        for after_id in self.root.tk.eval('after info').split():
            self.root.after_cancel(after_id)
        self.root.destroy()
        # for widget in self.main_frame.winfo_children():
        #    widget.destroy()
        # self.main_frame.destroy()
