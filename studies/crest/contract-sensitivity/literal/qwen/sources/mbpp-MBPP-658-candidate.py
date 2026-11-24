
from collections import Counter


def max_occurrences(list1):
	return Counter(list1).most_common(1)[0][0]
