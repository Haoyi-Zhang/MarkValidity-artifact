def capitalize_first_last_letters(str1):
	return str.join(' ', [word[1:len(word) - 1] + word[0].upper() + word[-1].upper() if 1 < len(word) else word.upper() for word in str1.split()])
