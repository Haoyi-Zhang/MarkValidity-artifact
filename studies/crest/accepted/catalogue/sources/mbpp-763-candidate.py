def find_min_diff(arr, n): 
	arr = sorted(arr) 
	diff = 10**20 
	for i in range(n - 1): 
		diff = min(diff, arr[i + 1] - arr[i])
	return diff
