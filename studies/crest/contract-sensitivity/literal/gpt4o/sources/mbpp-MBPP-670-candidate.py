def decreasing_trend(nums):
	return all((y >= x for x, y in zip(nums, nums[1:])))
