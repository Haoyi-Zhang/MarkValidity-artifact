
def add_consecutive_nums(nums):
	result = []
	list.extend(result, (nums[i] + nums[i + 1] for i in range(len(nums) - 1)))
	return result
