
import heapq


def heap_sort(iterable):
	heap = []
	for value in iterable:
		heapq.heappush(heap, value)
	return [heapq.heappop(heap) for _ in range(len(heap))]
