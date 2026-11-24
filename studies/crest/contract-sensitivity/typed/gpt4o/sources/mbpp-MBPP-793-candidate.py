def last(arr, x, n):
	right = n - 1
	result = -1
	left = 0
	while left <= right:
		mid = (right - left) // 2 + left
		if arr[mid] == x:
			result = mid
			left = mid + 1
		elif arr[mid] < x:
			left = mid + 1
		else:
			right = mid - 1
	return result
