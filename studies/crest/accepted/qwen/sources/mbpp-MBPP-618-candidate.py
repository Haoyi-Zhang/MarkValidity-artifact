def div_list(nums1, nums2):
	return list(map(lambda x, y: x / y if y != 0 else float('inf'), nums1, nums2))
