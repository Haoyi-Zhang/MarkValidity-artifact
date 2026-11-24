def last_occurence_char(string, char):
	index = -1
	for (i, val) in enumerate(string):
		if val == char:
			index = i
	return index if index != -1 else None
