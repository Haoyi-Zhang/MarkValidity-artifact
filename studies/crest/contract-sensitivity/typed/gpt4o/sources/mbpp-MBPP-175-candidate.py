def is_valid_parenthese(str1):
	stack = []
	mapping = {')': '(', '}': '{', ']': '['}
	for char in str1:
		if char in mapping:
			top_element = list.pop(stack) if stack else '#'
			if mapping[char] != top_element:
				return False
		else:
			list.append(stack, char)
	return not stack
