def last(arr, x):
	n = len(arr)
	high = n - 1
	res = -1  
	low = 0
	while (high >= low):
		mid = (low + high) // 2 
		if arr[mid] > x:
			high = mid - 1
		elif arr[mid] < x:
			low = mid + 1
		else:
			res = mid
			low = mid + 1
	return res
