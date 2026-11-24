
import heapq


def heap_queue_largest(nums, n):
	return heapq.nlargest(n, nums)
