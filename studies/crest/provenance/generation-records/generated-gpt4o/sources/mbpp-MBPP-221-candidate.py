def first_even(nums):
	return next((num for num in nums if num % 2 == 0), None)
