
from collections import OrderedDict

def remove_duplicate(string):
    words = string.split()
    unique_words = list(OrderedDict.fromkeys(words))
    return ' '.join(unique_words)
