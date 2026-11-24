

def  encode_cyclic(s: str):
    """
    returns encoded string by cycling groups of three characters.
    """
    # split string to groups. Each of length 3.
    groups = []
    for i in range((len(s) + 2) // 3):
        groups.append(s[(3 * i):min((3 * i + 3), len(s))])
    # cycle elements in each group. Unless group has fewer elements than 3.
    groups = [(group[1:] + group[0]) if 3 == len(group) else group for group in groups]
    return  "".join(groups)


def  decode_cyclic(s: str):
    """
    takes as input string encoded with encode_cyclic function. Returns decoded string.
    """
    return  encode_cyclic(encode_cyclic(s))