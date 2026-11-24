def dict_depth(d):
	if isinstance(d, dict):
		return (max(map(dict_depth, d.values())) if d else 0) + 1
	return 0
