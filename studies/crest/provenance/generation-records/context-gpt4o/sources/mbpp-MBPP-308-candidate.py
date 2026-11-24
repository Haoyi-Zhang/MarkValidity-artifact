def large_product(nums1, nums2, N):
	from heapq import nlargest
	products = [y * x for x in nums1 for y in nums2]
	return nlargest(N, products)
