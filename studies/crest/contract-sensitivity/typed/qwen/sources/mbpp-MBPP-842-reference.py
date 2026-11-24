
from collections import Counter

def get_odd_occurence(arr, arr_size):
    count = Counter(arr)
    for num, freq in count.items():
        if freq % 2 != 0:
            return num
    return None  # or raise an exception if no such number exists
