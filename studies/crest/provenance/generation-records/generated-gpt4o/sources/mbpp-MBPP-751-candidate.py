def check_min_heap(arr, i):
	n = len(arr)
	if i >= (n - 2) // 2:
		return True
	if arr[i] <= arr[i * 2 + 1] and (i * 2 + 2 == n or arr[i] <= arr[i * 2 + 2]):
		return check_min_heap(arr, i * 2 + 1) and (i * 2 + 2 == n or check_min_heap(arr, i * 2 + 2))
	return False
