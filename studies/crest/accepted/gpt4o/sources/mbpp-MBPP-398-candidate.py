def sum_of_digits(nums):
	return sum((sum((int(digit) for digit in str(abs(item)))) for item in nums if isinstance(item, int)))
