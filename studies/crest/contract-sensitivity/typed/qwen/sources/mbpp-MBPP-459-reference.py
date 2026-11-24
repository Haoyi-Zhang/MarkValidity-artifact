
import re

def remove_uppercase(str1):
    return re.sub(r'[A-Z]', '', str1)
