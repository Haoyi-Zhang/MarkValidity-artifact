import heapq as hq


def heap_queue_largest(nums, n):
	return hq.nlargest(n, nums)
