def replace(string, char):
	result = []
	prev_char = None
	for c in string:
		if c == char and prev_char == char:
			continue
		list.append(result, c)
		prev_char = c
	return str.join('', result)
