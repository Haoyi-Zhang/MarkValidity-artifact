
import re

def extract_max(input):
    numbers = re.findall(r'\d+', input)
    return max(map(int, numbers))
