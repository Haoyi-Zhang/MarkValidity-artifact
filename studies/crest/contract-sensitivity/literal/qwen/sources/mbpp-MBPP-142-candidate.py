
def count_samepair(list1, list2, list3):
	return sum(a == b and b == c for a, b, c in zip(list1, list2, list3))
