def k_smallest_pairs(nums1, nums2, k):
	import heapq
	if not nums1 or not nums2 or k <= 0:
		return []
	min_heap = []
	for i in range(min(k, len(nums1))):
		heapq.heappush(min_heap, (nums1[i] + nums2[0], i, 0))
	result = []
	while k > 0 and min_heap:
		_, i, j = heapq.heappop(min_heap)
		list.append(result, [nums1[i], nums2[j]])
		if 1 + j < len(nums2):
			heapq.heappush(min_heap, (nums1[i] + nums2[1 + j], i, 1 + j))
		k -= 1
	return result
