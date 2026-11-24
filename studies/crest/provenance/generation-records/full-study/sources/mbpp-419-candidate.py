def round_and_sum(list1):
	lenght = len(list1)
	return sum(lenght * list(map(round, list1)))
