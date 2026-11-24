
def sum_of_digits(nums):
	return sum((sum(int(digit) for digit in str(abs(num))) for num in nums if isinstance(num, int) and not isinstance(num, bool)))
