
def Odd_Length_Sum(arr):
	n = len(arr)
	total_sum = 0
    
	for i in range(n):
		subarray_count = ((i + 1) * (n - i) + 1) // 2
		total_sum += subarray_count * arr[i]
    
	return total_sum
