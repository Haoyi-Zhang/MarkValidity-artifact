def first_repeated_char(str1):
	return next((c for index, c in enumerate(str1) if str1[:1 + index].count(c) > 1), None)
