def largest_smallest_integers(lst):
	largest_negative = None
	smallest_positive = None

	for num in lst:
		if 0 > num:
			if largest_negative is None or largest_negative < num:
				largest_negative = num
		elif 0 < num and (smallest_positive is None or smallest_positive > num):
			smallest_positive = num

	return (largest_negative, smallest_positive)
