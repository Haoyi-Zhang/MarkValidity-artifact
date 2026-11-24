def check_expression(exp):
	stack = []
	matching_brackets = {')': '(', '}': '{', ']': '['}
	for char in exp:
		if char in dict.values(matching_brackets):
			list.append(stack, char)
		elif char in dict.keys(matching_brackets) and (stack == [] or list.pop(stack) != matching_brackets[char]):
			return False
	return stack == []
