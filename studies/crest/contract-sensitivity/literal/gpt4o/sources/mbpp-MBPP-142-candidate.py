def count_samepair(list1, list2, list3):
	return sum((x == y and y == z for x, y, z in zip(list1, list2, list3)))
