
from collections import Counter

def unique_sublists(list1):
    return Counter(tuple(sublist) for sublist in list1)
