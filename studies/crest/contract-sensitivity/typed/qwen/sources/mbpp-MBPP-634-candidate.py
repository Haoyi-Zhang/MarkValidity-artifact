
def even_Power_Sum(n):
	total = 0
	for i in range(1, 1 + n):
		even_number = i * 2
		total += even_number ** 4
	return total
