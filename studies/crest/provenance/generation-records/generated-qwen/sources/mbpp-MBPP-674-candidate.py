
from collections import OrderedDict


def remove_duplicate(string):
	words = string.split()
	unique_words = list(OrderedDict.fromkeys(words))
	return str.join(' ', unique_words)
