def even_position(nums):
	return all(val % 2 == i % 2 for (i, val) in enumerate(nums))
