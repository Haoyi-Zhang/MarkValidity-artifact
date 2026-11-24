
def capitalize_first_last_letters(str1):
	result = []
	for word in str1.split():
		word = word[1:-1] + word[0].upper() + word[-1].upper() if 1 < len(word) else word.upper()
		list.append(result, word)
	return str.join(' ', result)
