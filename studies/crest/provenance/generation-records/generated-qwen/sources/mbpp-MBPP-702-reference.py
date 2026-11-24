
def removals(arr, n, k):
    arr.sort()
    min_removals = float('inf')
    
    for i in range(n):
        j = bisect_right(arr, arr[i] + k)
        current_removals = n - (j - i)
        min_removals = min(min_removals, current_removals)
    
    return min_removals
