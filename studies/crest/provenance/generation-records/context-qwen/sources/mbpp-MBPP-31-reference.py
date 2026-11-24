
from collections import Counter
import heapq

def func(nums, k):
    count = Counter(num for sublist in nums for num in sublist)
    return [num for num, _ in heapq.nlargest(k, count.items(), key=lambda x: x[1])]
