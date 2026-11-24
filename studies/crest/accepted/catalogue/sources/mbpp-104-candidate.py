def sort_sublists(input_list):
	return [sorted(x, key=lambda x: x[0]) for x in input_list]
