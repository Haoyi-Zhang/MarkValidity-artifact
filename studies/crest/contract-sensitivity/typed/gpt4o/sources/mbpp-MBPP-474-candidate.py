def replace_char(str1, ch, newch):
	return str.join('', [newch if char == ch else char for char in str1])
