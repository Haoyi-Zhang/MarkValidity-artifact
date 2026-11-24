def drop_empty(dict1):
	return {key: value for (key, value) in dict1.items() if value is not None}
