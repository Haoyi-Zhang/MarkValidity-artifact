def find_lists(Input):
	return sum((isinstance(item, list) for item in Input))
