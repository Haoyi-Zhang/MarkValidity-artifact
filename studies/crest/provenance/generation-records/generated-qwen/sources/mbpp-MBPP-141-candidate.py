
def pancake_sort(nums):
	def flip(sublist, k):
		start = 0
		while start < k:
			sublist[start], sublist[k] = sublist[k], sublist[start]
			start += 1
			k -= 1

	n = len(nums)
	for size in range(n, 1, -1):
		max_index = nums.index(max(nums[:size]))
		if max_index != size - 1:
			if max_index != 0:
				flip(nums, max_index)
			flip(nums, size - 1)
	return nums
