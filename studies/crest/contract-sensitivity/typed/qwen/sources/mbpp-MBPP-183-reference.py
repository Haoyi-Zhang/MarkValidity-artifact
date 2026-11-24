
def count_pairs(arr, n, k):
    arr.sort()
    i, j = 0, 1
    count = 0
    
    while i < n and j < n:
        if arr[j] - arr[i] == k:
            count += 1
            j += 1
        elif arr[j] - arr[i] < k:
            j += 1
        else:
            i += 1
            
        if i == j:
            j += 1
    
    return count
