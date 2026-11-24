
def remove_column(list1, n):
	return [[val for (i, val) in enumerate(row) if i != n] for row in list1]
