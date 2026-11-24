
def comb_sort(nums):
	def get_next_gap(gap):
		gap = (gap * 10) // 13
		if 1 > gap:
			return 1
		return gap

	n = len(nums)
	gap = n
	swapped = True

	while gap != 1 or swapped:
		gap = get_next_gap(gap)
		swapped = False

		for i in range(n - gap):
			if nums[i] > nums[i + gap]:
				nums[i], nums[i + gap] = nums[i + gap], nums[i]
				swapped = True

	return nums
