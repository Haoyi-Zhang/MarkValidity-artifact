import heapq as hq


def heap_sort(iterable):
	h = []
	for value in iterable:
		hq.heappush(h, value)
	return [hq.heappop(h) for _ in range(len(h))]
