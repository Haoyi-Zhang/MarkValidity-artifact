
import heapq

def heap_sort(iterable):
    heap = []
    for value in iterable:
        heapq.heappush(heap, value)
    sorted_list = [heapq.heappop(heap) for _ in range(len(heap))]
    return sorted_list
