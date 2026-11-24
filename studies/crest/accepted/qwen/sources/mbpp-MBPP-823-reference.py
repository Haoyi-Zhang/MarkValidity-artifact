
import re

def check_substring(string, sample) :
    if re.match(f"^{re.escape(sample)}", string):
        return 'string starts with the given substring'
    else:
        return 'string doesnt start with the given substring'
