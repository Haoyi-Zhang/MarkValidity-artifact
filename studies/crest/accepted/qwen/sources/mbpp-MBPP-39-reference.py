
from collections import Counter
import heapq

def rearange_string(S):
    # Create a max heap based on the frequency of each character
    max_heap = [(-freq, char) for char, freq in Counter(S).items()]
    heapq.heapify(max_heap)
    
    # This will store the rearranged string
    result = []
    
    while len(max_heap) > 1:
        # Pop two most frequent characters
        freq1, char1 = heapq.heappop(max_heap)
        freq2, char2 = heapq.heappop(max_heap)
        
        # Append them to the result
        result.append(char1)
        result.append(char2)
        
        # Decrease their frequency and push back if still greater than 0
        if freq1 + 1 < 0:
            heapq.heappush(max_heap, (freq1 + 1, char1))
        if freq2 + 1 < 0:
            heapq.heappush(max_heap, (freq2 + 1, char2))
    
    # If there's one character left in the heap
    if max_heap:
        if max_heap[0][0] < -1:
            return ""
        else:
            result.append(max_heap[0][1])
    
    return "".join(result)
