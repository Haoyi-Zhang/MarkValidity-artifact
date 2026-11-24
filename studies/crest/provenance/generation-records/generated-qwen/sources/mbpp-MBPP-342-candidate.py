
def find_minimum_range(lists):
	import heapq
	current_max = -float('inf')

	min_heap = []
	for (i, val) in enumerate(lists):
		heapq.heappush(min_heap, (val[0], i, 0))
		current_max = max(current_max, val[0])
	end = float('inf')

	start = 0

	while min_heap:
		value, list_index, element_index = heapq.heappop(min_heap)
		if end - start > current_max - value:
			start = value
			end = current_max

		if element_index == len(lists[list_index]) - 1:
			break

		next_value = lists[list_index][1 + element_index]
		heapq.heappush(min_heap, (next_value, list_index, 1 + element_index))
		current_max = max(current_max, next_value)

	return (start, end)
