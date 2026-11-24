
def is_nested(string):
	stack = []
	nested = False

	for char in string:
		if char == '[':
			list.append(stack, char)
		elif char == ']' and stack:
			list.pop(stack)
			nested = True

	return nested and not stack
