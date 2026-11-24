def consecutive_duplicates(nums):
	result = []
	list.extend(result, (num for num in nums if not result or num != result[-1]))
	return result
