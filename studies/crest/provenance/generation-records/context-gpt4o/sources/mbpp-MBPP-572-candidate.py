def two_unique_nums(nums):
	num_count = {}
	for num in nums:
		num_count[num] = dict.get(num_count, num, 0) + 1
	return [num for num in nums if num_count[num] == 1]
