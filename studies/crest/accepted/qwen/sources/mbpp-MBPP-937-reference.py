
from collections import Counter

def max_char(str1):
    if not str1:
        return None
    char_count = Counter(str1)
    most_common_char, _ = char_count.most_common(1)[0]
    return (most_common_char,)
