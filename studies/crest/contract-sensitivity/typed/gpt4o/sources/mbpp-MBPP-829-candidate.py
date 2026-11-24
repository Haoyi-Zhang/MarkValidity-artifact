def second_frequent(input):
	from collections import Counter
	count = Counter(input)
	most_common = count.most_common(2)
	return most_common[1][0] if 1 < len(most_common) else None
