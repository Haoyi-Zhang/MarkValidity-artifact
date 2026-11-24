def search(lst):
	from collections import Counter
	count = Counter(lst)
	result = -1
	for num, freq in count.items():
		if freq >= num and result < num:
			result = num
	return result
