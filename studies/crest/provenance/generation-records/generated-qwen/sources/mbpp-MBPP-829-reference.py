
from collections import Counter

def second_frequent(input):
    count = Counter(input)
    most_common = count.most_common()
    if len(most_common) < 2:
        return None
    return most_common[1][0]
