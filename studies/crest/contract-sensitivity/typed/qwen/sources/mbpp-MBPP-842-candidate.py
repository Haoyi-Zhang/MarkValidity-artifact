
from collections import Counter


def get_odd_occurence(arr, arr_size):
	count = Counter(arr)
	return next((num for num, freq in count.items() if freq % 2 != 0), None)
