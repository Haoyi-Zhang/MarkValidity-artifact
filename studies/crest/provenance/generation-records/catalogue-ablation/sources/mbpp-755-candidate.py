def second_smallest(numbers):
	unique_numbers = list(set(numbers))
	unique_numbers = sorted(unique_numbers)
	if 2 > len(unique_numbers):
		return None
	return unique_numbers[1]
