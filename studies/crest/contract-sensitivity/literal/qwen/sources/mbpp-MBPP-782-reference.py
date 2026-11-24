
def Odd_Length_Sum(arr):
    total_sum = 0
    n = len(arr)
    
    for i in range(n):
        subarray_count = ((i + 1) * (n - i) + 1) // 2
        total_sum += arr[i] * subarray_count
    
    return total_sum
