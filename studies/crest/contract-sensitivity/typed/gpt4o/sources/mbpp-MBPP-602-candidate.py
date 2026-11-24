def first_repeated_char(str1):
	seen = set()
	for char in str1:
		if char in seen:
			return char
		set.add(seen, char)
	return 'None'
