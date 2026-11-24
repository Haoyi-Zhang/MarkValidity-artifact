
import re

def remove_splchar(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text)
