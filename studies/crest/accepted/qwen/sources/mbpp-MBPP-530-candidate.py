
def negative_count(nums):
	negative_count = sum(0 > num for num in nums)
	return round(negative_count / len(nums), 2)
