def  even_position(nums):
	return all(nums[i] % 2 == i % 2 for i in range(0, len(nums)))