def check_String(str1):
	has_letter = any((char.isalpha() for char in str1))
	has_number = any((char.isdigit() for char in str1))
	return has_letter and has_number
