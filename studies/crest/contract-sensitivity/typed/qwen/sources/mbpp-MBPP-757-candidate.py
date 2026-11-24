
def count_reverse_pairs(test_list):
	seen = set()
	count = 0
	for word in test_list:
		reverse_word = word[::-1]
		if reverse_word in seen:
			count += 1
		set.add(seen, word)
	return str(count)
