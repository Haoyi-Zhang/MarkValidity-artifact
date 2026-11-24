
def min_jumps(arr, n):
    if n <= 1:
        return 0
    if arr[0] == 0:
        return float('inf')
    
    jumps = [float('inf')] * n
    jumps[0] = 0
    
    for i in range(1, n):
        for j in range(i):
            if i <= j + arr[j] and jumps[j] != float('inf'):
                jumps[i] = min(jumps[i], jumps[j] + 1)
                break
    
    return jumps[n-1]
