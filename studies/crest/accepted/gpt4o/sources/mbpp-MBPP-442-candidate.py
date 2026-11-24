def positive_count(nums):
	positive_numbers = [num for num in nums if 0 < num]
	ratio = len(positive_numbers) / len(nums)
	return round(ratio, 2)
