def count_list(input_list):
	return sum((isinstance(item, list) for item in input_list))
