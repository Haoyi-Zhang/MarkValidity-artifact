
import re

def text_match_word(text):
    pattern = r'\b\w+\b[.!?]*$'
    if re.search(pattern, text):
        return 'Found a match!'
    else:
        return 'Not matched!'
