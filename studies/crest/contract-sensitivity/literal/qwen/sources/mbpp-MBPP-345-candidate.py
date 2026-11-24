
def diff_consecutivenums(nums):
	return [b - a for a, b in zip(nums, nums[1:])]
