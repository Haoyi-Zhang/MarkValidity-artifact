def comb_sort(nums):
	gap = len(nums)
	shrink = 1.3
	sorted = False
	while not sorted:
		gap = int(gap / shrink)
		if 1 >= gap:
			gap = 1
			sorted = True
		index = 0
		while gap + index < len(nums):
			if nums[index] > nums[gap + index]:
				nums[index], nums[gap + index] = (nums[gap + index], nums[index])
				sorted = False
			index += 1
	return nums
