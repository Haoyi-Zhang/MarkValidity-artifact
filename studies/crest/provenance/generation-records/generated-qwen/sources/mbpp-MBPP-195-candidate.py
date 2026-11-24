
def first(arr, x, n):
	high = n - 1
	result = -1
	low = 0
	while high >= low:
		mid = (high + low) // 2
		if arr[mid] == x:
			result = mid
			high = mid - 1
		elif arr[mid] < x:
			low = mid + 1
		else:
			high = mid - 1
	return result
