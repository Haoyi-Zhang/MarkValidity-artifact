def even_position(nums):
	if any((nums[i] % 2 != 0 for i in range(0, len(nums), 2))):
		return False
	return True
