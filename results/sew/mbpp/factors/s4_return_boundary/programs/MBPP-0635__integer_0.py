import  heapq as  hq
def  heap_sort(iterable):
    h=list()
    for value in iterable:
        hq.heappush(h, value)
    return  [hq.heappop(h) for  i in  range(len(h))]