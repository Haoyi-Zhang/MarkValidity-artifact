
import re

def check_literals(text, patterns):
    for pattern in patterns:
        if re.search(pattern, text):
            return 'Matched!'
    return 'Not Matched!'
