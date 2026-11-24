
def removals(arr, n, k):
	arr = sorted(arr)
	min_removals = float('inf')
    
	for i in range(n):
		j = bisect_right(arr, k + arr[i])
		current_removals = n - (j - i)
		min_removals = min(min_removals, current_removals)
    
	return min_removals
