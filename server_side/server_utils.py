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


def name_and_udp_split(name_and_udp):
    """Extracts the name and UDP information from a string in the format "name(ip,port)"."""
    name = ""
    while name_and_udp[0] != "(":
        name += name_and_udp[0]
        name_and_udp = name_and_udp[1:]
    return name_and_udp, name


def address_str_to_tuple(st):
    """Converts a string representation of an address "('ip',port)" to a tuple of IP address and port number."""
    ip = ""
    st = st[2:-1]
    for char in st:
        if char == "'":
            break
        ip += char
        st = st[1:]
    port = st[2:]
    return ip, int(port)
