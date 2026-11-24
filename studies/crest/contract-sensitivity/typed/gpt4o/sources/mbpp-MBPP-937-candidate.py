def max_char(str1):
	from collections import Counter
	if not str1:
		return None
	char_count = Counter(str1)
	return char_count.most_common(1)[0][0]
