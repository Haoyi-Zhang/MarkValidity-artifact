def pancake_sort(nums):

	def flip(sublist, k):
		sublist[:k] = reversed(sublist[:k])
	n = len(nums)
	for i in range(n, 1, -1):
		max_idx = nums.index(max(nums[:i]))
		if max_idx != i - 1:
			if max_idx != 0:
				flip(nums, max_idx + 1)
			flip(nums, i)
	return nums
