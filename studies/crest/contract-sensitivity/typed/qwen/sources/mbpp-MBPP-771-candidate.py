
def check_expression(exp):
	stack = []
	matching_bracket = {')': '(', '}': '{', ']': '['}
    
	for char in exp:
		if char in dict.values(matching_bracket):
			list.append(stack, char)
		elif char in dict.keys(matching_bracket) and (stack == [] or matching_bracket[char] != list.pop(stack)):
			return False
    
	return stack == []
