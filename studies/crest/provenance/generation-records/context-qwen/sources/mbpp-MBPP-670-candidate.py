
def decreasing_trend(nums):
	if any((nums[i] >= nums[i - 1] for i in range(1, len(nums)))):
		return True
	return False
