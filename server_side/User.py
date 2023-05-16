class User:
    def __init__(self, name, tcp_addr, is_manager, tcp_socket, udp_addr):
        """This class represents a user inside a meeting"""
        self.name = name
        self.tcp_address = tcp_addr
        self.udp_address = udp_addr
        self.is_manager = is_manager
        self.tcp_socket = tcp_socket
        self.allowed_camera = True
        self.allowed_screen = True
        self.allowed_microphone = True
        self.camera = False
        self.screen = False
        self.microphone = False

    def set_name(self, new_name):
        self.name = new_name

    def set_is_manager(self, new_is_manager):
        self.is_manager = new_is_manager

    def set_tcp_socket(self, new_socket):
        self.tcp_socket = new_socket

    def set_tcp_address(self, new_address):
        self.tcp_address = new_address

    def set_udp_address(self, new_address):
        self.udp_address = new_address

    def set_allowed_camera(self, var):
        self.allowed_camera = var

    def set_allowed_screen(self, var):
        self.allowed_screen = var

    def set_allowed_microphone(self, var):
        self.allowed_microphone = var

    def set_camera(self, var):
        self.camera = var

    def set_screen(self, var):
        self.screen = var

    def set_microphone(self, var):
        self.microphone = var

    def get_name(self):
        return self.name

    def get_udp_address(self):
        return self.udp_address

    def get_tcp_address(self):
        return self.tcp_address

    def get_tcp_socket(self):
        return self.tcp_socket

    def get_is_manager(self):
        return self.is_manager

    def get_allowed_camera(self):
        return self.allowed_camera

    def get_allowed_screen(self):
        return self.allowed_screen

    def get_allowed_microphone(self):
        return self.allowed_microphone

    def get_camera(self):
        return self.camera

    def get_screen(self):
        return self.screen

    def get_microphone(self):
        return self.microphone


    def __str__(self):
        return "name: " + self.name + "| udp_address: " + str(self.udp_address) + "| tcp_address: " \
               + str(self.tcp_address) + "| is_manager: " + str(self.is_manager)

    def __repr__(self):
        return str(self)
