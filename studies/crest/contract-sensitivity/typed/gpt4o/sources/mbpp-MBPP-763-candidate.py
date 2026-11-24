def find_Min_Diff(arr, n):
	if 2 > n:
		return None
	arr = sorted(arr)
	min_diff = float('inf')
	for i in range(n - 1):
		min_diff = min(min_diff, arr[i + 1] - arr[i])
	return min_diff
