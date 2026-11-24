def is_nested(string):
	open_count = 0
	nest_found = False
	for char in string:
		if char == '[':
			open_count += 1
		elif char == ']':
			if open_count <= 0:
				return False
			open_count -= 1
			if open_count > 0:
				nest_found = True
	return nest_found if open_count == 0 else False
