
def check_min_heap(arr, i):
	n = len(arr)
	if i * 2 + 2 > n:
		return True
	if arr[i] > arr[i * 2 + 1] or arr[i] > arr[i * 2 + 2]:
		return False
	return check_min_heap(arr, i * 2 + 1) and check_min_heap(arr, i * 2 + 2)
