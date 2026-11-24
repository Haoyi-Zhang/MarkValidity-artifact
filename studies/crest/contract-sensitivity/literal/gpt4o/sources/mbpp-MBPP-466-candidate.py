def find_peak(arr, n):
	return next((i for i in range(n) if (i == 0 or arr[i - 1] <= arr[i]) and (i == n - 1 or arr[i] >= arr[i + 1])), -1)
