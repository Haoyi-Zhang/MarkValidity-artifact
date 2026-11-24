
import heapq

def heap_queue_smallest(nums, n):
    return heapq.nsmallest(n, nums)
