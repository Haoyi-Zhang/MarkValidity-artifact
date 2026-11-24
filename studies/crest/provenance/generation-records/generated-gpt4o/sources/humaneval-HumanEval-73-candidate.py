def smallest_change(arr):
	n = len(arr)
	return sum((arr[i] != arr[n - i - 1] for i in range(n // 2)))
