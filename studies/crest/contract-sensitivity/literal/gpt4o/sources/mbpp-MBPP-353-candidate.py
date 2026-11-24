def remove_column(list1, n):
	return [row[:n] + row[1 + n:] for row in list1 if len(row) > n]
