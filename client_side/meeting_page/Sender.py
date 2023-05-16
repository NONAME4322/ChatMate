# Sender class:

class Sender:
    def __init__(self, udp_addr, name, name_label, is_manager_switch, is_manager_var, camera_option_menu, microphone_option_menu,
                 screen_option_menu, kick_btn, frame, canvas):
        self.name = name
        self.udp_address = udp_addr
        self.name_label = name_label
        self.allowed_camera = True
        self.allowed_microphone = True
        self.is_camera = False
        self.is_screen = False
        self.is_microphone = False
        self.is_manager_switch = is_manager_switch
        self.is_manager_var = is_manager_var
        self.camera_option_menu = camera_option_menu
        self.microphone_option_menu = microphone_option_menu
        self.screen_option_menu = screen_option_menu
        self.kick_btn = kick_btn
        self.frame = frame
        self.canvas = canvas

    def set_name(self, new_name):
        self.name = new_name
        self.name_label.config(text=new_name)

    def set_udp_address(self, new_address):
        self.udp_address = new_address

    def set_is_manager(self, var):
        self.is_manager_var.set(var)

    def set_camera(self, var):
        if self.camera_option_menu.get() != "hidden":
            if var:
                self.camera_option_menu.set("open")
            else:
                self.camera_option_menu.set("closed")
        self.is_camera = var

    def set_screen(self, var):
        if self.screen_option_menu.get() != "hidden":
            if var:
                self.screen_option_menu.set("open")
            else:
                self.screen_option_menu.set("closed")
        self.is_screen = var

    def set_microphone(self, var):
        if self.microphone_option_menu.get() != "hidden":
            if var:
                self.microphone_option_menu.set("open")
            else:
                self.microphone_option_menu.set("closed")
        self.is_microphone = var

    def set_camera_blocked(self, var, is_manager):
        if var:
            self.camera_option_menu.set("blocked")
            if is_manager:
                self.camera_option_menu.configure(values=["unblock"])
            else:
                self.camera_option_menu.configure(values=[])
        else:
            self.camera_option_menu.set("closed")
            if is_manager:
                self.camera_option_menu.configure(values=["hide", "block"])
            else:
                self.camera_option_menu.configure(values=["hide"])

    def set_microphone_blocked(self, var, is_manager):
        if var:
            self.microphone_option_menu.set("blocked")
            if is_manager:
                self.microphone_option_menu.configure(values=["unblock"])
            else:
                self.microphone_option_menu.configure(values=[])
        else:
            self.microphone_option_menu.set("closed")
            if is_manager:
                self.microphone_option_menu.configure(values=["hide", "block"])
            else:
                self.microphone_option_menu.configure(values=["hide"])

    def set_screen_blocked(self, var, is_manager):
        if var:
            self.screen_option_menu.set("blocked")
            if is_manager:
                self.screen_option_menu.configure(values=["unblock"])
            else:
                self.screen_option_menu.configure(values=[])
        else:
            self.screen_option_menu.set("closed")
            if is_manager:
                self.screen_option_menu.configure(values=["hide", "block"])
            else:
                self.screen_option_menu.configure(values=["hide"])

    def set_allowed_camera(self, var):
        self.allowed_camera = var

    def set_allowed_microphone(self, var):
        self.allowed_microphone = var

    def get_name(self):
        return self.name

    def get_is_manager(self):
        return bool(self.is_manager_switch.get())

    def get_camera(self):
        return self.is_camera

    def get_screen(self):
        return self.is_screen

    def get_microphone(self):
        return self.is_microphone

    def get_udp_address(self):
        return self.udp_address

    def get_frame(self):
        return self.frame

    def get_canvas(self):
        return self.canvas

    def get_allowed_camera(self):
        return self.allowed_camera

    def get_allowed_microphone(self):
        return self.allowed_microphone

    def get_name_label(self):
        return self.name_label

    def get_camera_option_menu(self):
        return self.camera_option_menu

    def get_microphone_option_menu(self):
        return self.microphone_option_menu

    def get_screen_option_menu(self):
        return self.screen_option_menu

    def get_option_menus(self):
        return [self.camera_option_menu, self.microphone_option_menu, self.screen_option_menu]

    def lock_my_widgets(self):
        """
        Locks the widgets of the sender, disabling interaction.

        This method disables the manager switch and hides the option menus and kick button.
        """

        self.is_manager_switch.configure(state="disabled")

        option_menus = [self.camera_option_menu, self.microphone_option_menu, self.screen_option_menu]
        for menu in option_menus:
            menu.configure(values=[])
        self.kick_btn.grid_forget()

    def lock_widgets(self):
        """
        Locks the widgets of the sender, disabling interaction.

        This method disables the manager switch and hides the kick button. Depending on the state of the
        option menus, it may also hide or disable them.
        """
        self.is_manager_switch.configure(state="disabled")
        self.kick_btn.grid_forget()

        self.screen_option_menu.configure(values=[])
        option_menus = [self.camera_option_menu, self.microphone_option_menu]
        for menu in option_menus:
            if menu.get() == "blocked":
                menu.configure(values=[])

            elif menu.get() == "hidden":
                pass

            else:
                menu.configure(values=["hide"])

    def unlock_widgets(self):
        """
        Unlocks the widgets of the sender, enabling interaction.

        This method enables the manager switch and shows the kick button. Depending on the state of the
        option menus, it may also enable or update their values.
        """
        self.is_manager_switch.configure(state="normal")
        info = self.name_label.grid_info()
        row = info['row']
        self.kick_btn.grid(row=row, column=5, padx=5, pady=5)

        option_menus = [self.camera_option_menu, self.microphone_option_menu]
        for menu in option_menus:
            if menu.get() == "blocked":
                menu.configure(values=["unblock"])

            elif menu.get() == "hidden":
                pass

            else:
                menu.configure(values=["hide", "block"])
        if self.screen_option_menu.get() == "blocked":
            self.screen_option_menu.configure(values=["unblock"])
        else:
            self.screen_option_menu.configure(values=["block"])

    def remove_from_commands(self):
        """
          Removes the sender's widgets from the display.

          This method removes the camera, microphone, screen option menus, name label, manager switch, and kick button
          from the display.
          """
        self.camera_option_menu.grid_forget()
        self.microphone_option_menu.grid_forget()
        self.screen_option_menu.grid_forget()
        self.name_label.grid_forget()
        self.is_manager_switch.grid_forget()
        self.kick_btn.grid_forget()

    def __str__(self):
        return "name: " + str(self.name) + "| udp_address: " + str(self.udp_address) + "| camera: " \
               + str(self.get_camera()) + "| screen: " + str(self.get_screen()) + "| microphone: " + str(
            self.get_microphone())

    def __repr__(self):
        return str(self)
