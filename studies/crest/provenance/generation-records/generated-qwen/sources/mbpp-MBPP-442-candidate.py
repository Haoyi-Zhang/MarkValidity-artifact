
def positive_count(nums):
	count = sum(0 < num for num in nums)
	return round(count / len(nums), 2)
