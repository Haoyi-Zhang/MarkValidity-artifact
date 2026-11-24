
def min_Ops(arr,n,k):
    arr.sort()
    median = arr[n // 2]
    total_ops = 0
    
    for num in arr:
        ops_needed = abs(num - median)
        if ops_needed % k != 0:
            return -1
        total_ops += ops_needed // k
    
    return total_ops
