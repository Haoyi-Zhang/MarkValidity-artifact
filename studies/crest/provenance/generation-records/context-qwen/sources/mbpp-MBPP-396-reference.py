
import re

def check_char(string):
    if re.match(r'^[a-zA-Z]([a-zA-Z]+)?\1$', string):
        return "Valid"
    else:
        return "Invalid"
