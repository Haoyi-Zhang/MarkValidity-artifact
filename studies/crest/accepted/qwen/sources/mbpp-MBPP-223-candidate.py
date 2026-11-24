
def is_majority(arr, n, x):
	if n == 0:
		return False
	mid = n // 2
	if arr[mid] == x:
		low = mid - mid // 2
		high = mid + mid // 2
		while low >= 0 and arr[low] == x:
			low -= 1
		while high < n and arr[high] == x:
			high += 1
		return high - low - 1 > n // 2
	elif mid == 0 or arr[mid - 1] != x:
		lo = mid + 1
	else:
		hi = mid - 1
