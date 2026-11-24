
def find_minimum_range(lists):
    import heapq

    min_heap = []
    current_max = -float('inf')
    for i in range(len(lists)):
        heapq.heappush(min_heap, (lists[i][0], i, 0))
        current_max = max(current_max, lists[i][0])

    start = 0
    end = float('inf')

    while min_heap:
        value, list_index, element_index = heapq.heappop(min_heap)
        if end - start > current_max - value:
            start = value
            end = current_max

        if element_index == len(lists[list_index]) - 1:
            break

        next_value = lists[list_index][element_index + 1]
        heapq.heappush(min_heap, (next_value, list_index, element_index + 1))
        current_max = max(current_max, next_value)

    return (start, end)
