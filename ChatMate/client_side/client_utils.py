import pyaudio

import re

from tkinter import PhotoImage


def address_str_to_tuple(st):
    """Converts a string representation of an address
    (in the format "('ip_address', port)") to a tuple of the IP address and port."""
    ip = ""
    st = st[2:-1]
    for char in st:
        if char == "'":
            break
        ip += char
        st = st[1:]
    port = st[2:]
    return ip, int(port)


def two_address_str_to_two_tuples(st):
    """Converts a string representation of two addresses (in the format
    "('(ip_address1', port1)', '(ip_address2', port2)')") to two tuples of IP addresses and ports."""
    st = st[1:-1]
    str_tuple1 = ""
    for char in st:
        str_tuple1 += char
        st = st[1:]
        if char == ")":
            break
    str_tuple2 = st[2:]

    return address_str_to_tuple(str_tuple1), address_str_to_tuple(str_tuple2)


def canvas_close_camera(canvas):
    """ Closes the camera on a Tkinter canvas by creating a black rectangle and displaying a text overlay."""
    # window.update()
    rect = canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(), fill="black")
    text = canvas.create_text(canvas.winfo_width() / 2, canvas.winfo_height() / 2, text="camera is closed",
                              fill="white", font=("sans-serif", int(canvas.winfo_width() / 15), "bold"))
    canvas.bind("<Configure>", lambda event: resize_rectangle(event, canvas, rect, text))

    # Callback function for the <Configure> event
    def resize_rectangle(event, canvas, rectangle, text):
        # Get the new dimensions of the canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # Update the coordinates of the rectangle to match the new dimensions of the canvas
        canvas.coords(rectangle, 0, 0, canvas_width, canvas_height)
        canvas.coords(text, canvas_width / 2, canvas_height / 2)
        canvas.itemconfigure(text, font=("sans-serif", int(canvas.winfo_width() / 15), "bold"))


# this function gets the number of users and window sizes
# this function returns the size of each video and how to arrange the video on a grid optimally
def optimal_layout(window_width, window_height, user_num, buttons_height):
    width_sizes = []
    height_sizes = []
    options = []
    for i in range(user_num):
        width_sizes.append(window_width / (i + 1) - 20)
        height_sizes.append((window_height - buttons_height * 2) / (i + 1) - 10)

    for i in range(user_num):
        for j in range(user_num):
            if (i + 1) * (j + 1) == user_num or (i + 1) * (j + 1) > user_num:
                options.append((min(width_sizes[i], height_sizes[j] * 16 / 9), (i + 1), j + 1))
    maximum = 0
    best_option = (0, 0, 0)
    for option in options:
        if option[0] > maximum:
            maximum = option[0]
            best_option = option
    return best_option


def str_to_bool(st):
    """ Converts a string representation of a boolean value ("True" or "False") to a corresponding boolean."""
    if st == 'True':
        return True
    elif st == 'False':
        return False


def str_to_list(st):
    """Converts a string representation of a list (in the format "[item1, item2, ...]") to an actual list."""
    st = st[1:-1]
    temp = ""
    lst = []
    flag = False

    for char in st:
        if char == '(':
            flag = True
            temp += char
        elif char == ')':
            flag = False
            temp += char
        elif char == '"':
            pass
        elif char == "'" or char == ' ':
            if flag:
                temp += char
        elif char != ',':
            temp += char
        else:
            if not flag:
                lst.append(temp)
                temp = ""
            else:
                temp += char
    lst.append(temp)
    return lst


# this function returns the end of a packet until $SEP$ sign
# it allows me to receive relevant data such as the packet number
# without damaging the original packet
def split_packet(packet):
    char = packet[-1:]
    my_data = ""
    while packet[-5:] != b'$SEP$' and packet.__len__() > 0:
        my_data = str(char.decode()) + my_data
        packet = packet[0:-1]
        char = packet[-1:]
    packet = packet[0:-1]

    return packet[:-4], my_data


# this function creates a sound stream that can be played by your speaker
def output_sound_stream(p):
    output = p.open(
        format=p.get_format_from_width(2),
        channels=2,
        rate=16000,
        output=True,
        frames_per_buffer=3200)
    return output


# this function create a sound stream that records your device mic
def input_sound_stream(p):
    input_stream = p.open(
        format=pyaudio.paInt16,
        channels=2,
        rate=16000,
        input=True,
        frames_per_buffer=3200)
    return input_stream


def photo_image(img):
    """ Converts an image array (img) to a Tkinter PhotoImage object."""
    h, w = img.shape[:2]
    data = f'P6 {w} {h} 255 '.encode() + img[..., ::-1].tobytes()
    return PhotoImage(width=w, height=h, data=data, format='PPM')


def split_packet_without_decode(packet):
    """Splits a packet until the "$SEP$" sign and returns the remaining packet and the extracted data as bytes.
    Similar to split_packet(), but it doesn't decode the extracted data."""
    char = packet[-1:]
    my_data = b''
    while packet[-5:] != b'$SEP$' and packet.__len__() > 0:
        my_data = char + my_data
        packet = packet[0:-1]
        char = packet[-1:]
    packet = packet[0:-1]

    return packet[:-4], my_data


def is_alphanumeric(input_str):
    """Checks whether a string (input_str) contains only alphanumeric characters (letters and digits)."""
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    return pattern.match(input_str) is not None
