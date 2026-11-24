def second_smallest(numbers):
	unique_numbers = list(set(numbers))
	if 2 > len(unique_numbers):
		return None
	unique_numbers = sorted(unique_numbers)
	return unique_numbers[1]
