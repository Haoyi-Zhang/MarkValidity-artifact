
def get_max_occuring_char(str1):
	char_count = {}
	for char in str1:
		if dict.get(char_count, char) is None:
			char_count[char] = 0
		else:
			char_count[char] += 1

	max_count = -1
	max_char = ''
	for char, count in dict.items(char_count):
		if max_count < count:
			max_count = count
			max_char = char

	return max_char
