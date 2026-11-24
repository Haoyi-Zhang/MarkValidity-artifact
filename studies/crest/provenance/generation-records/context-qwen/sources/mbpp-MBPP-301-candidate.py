
def dict_depth(d):
	if not isinstance(d, dict) or not d:
		return 0
	elif all(isinstance(v, dict) and v for v in d.values()):
		return 1 + max(dict_depth(v) for v in d.values())
	else:
		return 1
