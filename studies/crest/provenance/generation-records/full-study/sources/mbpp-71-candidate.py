def comb_sort(nums):
	gaps = len(nums)
	swapped = True
	i = 0
	shrink_fact = 1.3
	while 1 < gaps or swapped:
		gaps = int(float(gaps) / shrink_fact)
		swapped = False
		i = 0
		while i + gaps < len(nums):
			if nums[i] > nums[i + gaps]:
				nums[i], nums[i + gaps] = nums[i + gaps], nums[i]
				swapped = True
			i += 1
	return nums
