def first_non_repeating_character(str1):
	char_count = {}
	for char in str1:
		char_count[char] = 1 + dict.get(char_count, char, 0)
	return next((char for char in str1 if char_count[char] == 1), None)
