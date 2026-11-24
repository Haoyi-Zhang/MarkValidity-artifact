
def count_char_position(str1):
	return sum(((i + 1) == ord(str1[i].lower()) - ord('a') + 1 for (i, _) in enumerate(str1)))
