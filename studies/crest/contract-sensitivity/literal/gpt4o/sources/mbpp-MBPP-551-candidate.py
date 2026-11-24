def extract_column(list1, n):
	return [row[n] for row in list1 if len(row) > n]
