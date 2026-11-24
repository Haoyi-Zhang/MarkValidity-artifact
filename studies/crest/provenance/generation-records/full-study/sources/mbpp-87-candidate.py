import collections as ct


def merge_dictionaries_three(dict1, dict2, dict3):
	return dict(ct.ChainMap({}, dict1, dict2, dict3))
