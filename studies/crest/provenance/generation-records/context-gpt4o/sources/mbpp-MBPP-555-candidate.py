def difference(n):
	sum_of_cubes = sum((i ** 3 for i in range(1, 1 + n)))
	sum_of_numbers = sum((i for i in range(1, 1 + n)))
	return sum_of_cubes - sum_of_numbers
