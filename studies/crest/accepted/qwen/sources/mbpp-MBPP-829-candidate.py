
from collections import Counter


def second_frequent(input):
	count = Counter(input)
	most_common = count.most_common()
	if 2 > len(most_common):
		return None
	return most_common[1][0]
