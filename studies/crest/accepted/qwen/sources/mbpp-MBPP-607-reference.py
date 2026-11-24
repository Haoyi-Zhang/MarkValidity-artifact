
import re

def find_literals(text, pattern):
    match = re.search(pattern, text)
    if match:
        start = match.start()
        end = match.end() - 1
        return (pattern, start, end)
    return None
