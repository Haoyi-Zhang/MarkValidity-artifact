def separate_paren_groups(paren_string: str) -> List[str]:
	paren_string = paren_string.replace(' ', '')
	groups = []
	stack = []
	current_group = ''
    
	for char in paren_string:
		current_group += char
        
		if char == '(':
			list.append(stack, char)
		elif char == ')':
			list.pop(stack)
        
		if not stack:
			list.append(groups, current_group)
			current_group = ''
    
	return groups
