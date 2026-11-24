
import re

def find_adverb_position(text):
    adverbs = re.finditer(r"\w+ly", text)
    results = [(match.start(), match.end(), match.group()) for match in adverbs]
    return results
