
import re

def check_IP(Ip):
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(pattern, Ip):
        octets = Ip.split('.')
        if all(0 <= int(octet) <= 255 for octet in octets):
            return 'Valid IP address'
    return 'Invalid IP address'
