import re
def  occurance_substring(text,pattern):
 for match in re.finditer(pattern, text):
    s, e = match.start(), match.end()
    return (text[s:e], s, e)
