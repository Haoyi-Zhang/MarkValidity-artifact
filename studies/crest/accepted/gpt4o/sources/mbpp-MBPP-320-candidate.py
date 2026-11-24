def sum_difference(n):
	sum_of_numbers = n * (1 + n) // 2
	squared_sum = sum_of_numbers ** 2
	sum_of_squares = sum((i ** 2 for i in range(1, 1 + n)))
	return squared_sum - sum_of_squares
