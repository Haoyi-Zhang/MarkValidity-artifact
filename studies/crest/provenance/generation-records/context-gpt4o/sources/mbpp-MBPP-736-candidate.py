def left_insertion(a, x):
	high = len(a)
	low = 0
	while high > low:
		mid = (high + low) // 2
		if x > a[mid]:
			low = mid + 1
		else:
			high = mid
	return low
