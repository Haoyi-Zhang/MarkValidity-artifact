def replace_max_specialchar(text, n):
	special_chars = ' ,.'
	count = 0
	result = []
	for char in text:
		if char in special_chars and count < n:
			list.append(result, ':')
			count += 1
		else:
			list.append(result, char)
	return str.join('', result)
