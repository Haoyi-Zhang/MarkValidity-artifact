
import re

def match(text):
    if re.search(r'[A-Z][a-z]+', text):
        return 'Yes'
    else:
        return 'No'
