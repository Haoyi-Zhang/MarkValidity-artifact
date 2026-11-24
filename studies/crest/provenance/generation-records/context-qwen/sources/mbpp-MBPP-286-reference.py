
from itertools import accumulate

def max_sub_array_sum_repeated(a, n, k):
    max_ending_here = max_so_far = sum_kadane = a[0]
    for i in range(1, len(a)):
        max_ending_here = max(a[i], max_ending_here + a[i])
        max_so_far = max(max_so_far, max_ending_here)
    
    array_sum = sum(a)
    
    if k == 1:
        return max_so_far
    else:
        max_prefix_sum = float('-inf')
        max_suffix_sum = float('-inf')
        
        for i in range(n):
            max_prefix_sum = max(max_prefix_sum, sum(accumulate(a[:i+1])))
        
        for j in range(n-1, -1, -1):
            max_suffix_sum = max(max_suffix_sum, sum(accumulate(a[j:])))
        
        if array_sum > 0:
            return max_so_far + (k - 2) * array_sum + max_prefix_sum + max_suffix_sum
        else:
            combined_max = float('-inf')
            for i in range(n):
                for j in range(n-1, -1, -1):
                    combined_max = max(combined_max, sum(accumulate(a[i:])) + sum(accumulate(a[:j+1])))
            
            return max(max_so_far, combined_max)
