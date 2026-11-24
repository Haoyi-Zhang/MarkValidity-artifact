
def find_missing(ar, N):
	high = N - 1
	low = 0
	while high > low:
		mid = (high + low) // 2
		if ar[mid] == mid + 1:
			low = mid + 1
		else:
			high = mid
	return low + 1
