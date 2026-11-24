
def average_tuple(nums):
	return [sum(row[i] for row in nums) / len(nums) for (i, _) in enumerate(nums[0])]
