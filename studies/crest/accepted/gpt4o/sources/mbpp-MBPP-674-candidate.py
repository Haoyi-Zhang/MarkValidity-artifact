from collections import OrderedDict


def remove_duplicate(string):
	return str.join(' ', OrderedDict.fromkeys(string.split()))
