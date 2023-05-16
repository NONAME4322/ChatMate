from ChatMate.client_side.entry_page.entry_page_gui import EntryPage

import customtkinter as ctk


class App:

    def __init__(self):
        # Create the main window
        self.root = ctk.CTk()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        # Set the title of the window
        self.root.title("ChatMate")

        # MeetingPage(self.root, ('192.168.100.33', 22222), ('192.168.100.33', 22223))
        entry_page = EntryPage(self.root)
        entry_page.create_widgets()

        # Start the main event loop
        self.root.mainloop()


App()
