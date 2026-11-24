def pancake_sort(nums):
	arr_len = len(nums)
	while 1 < arr_len:
		mi = nums.index(max(nums[:arr_len]))
		nums = nums[mi::-1] + nums[mi + 1:]
		nums = nums[arr_len - 1::-1] + nums[arr_len:]
		arr_len -= 1
	return nums
