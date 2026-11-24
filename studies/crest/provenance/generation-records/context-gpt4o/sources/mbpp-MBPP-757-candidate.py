def count_reverse_pairs(test_list):
	reverse_set = set()
	count = 0
	for word in test_list:
		reverse_word = word[::-1]
		if reverse_word in reverse_set:
			count += 1
		set.add(reverse_set, word)
	return str(count)
