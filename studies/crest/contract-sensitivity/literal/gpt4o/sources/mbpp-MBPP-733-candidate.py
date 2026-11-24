def find_first_occurrence(A, x):
	high = len(A) - 1
	result = -1
	low = 0
	while high >= low:
		mid = (high + low) // 2
		if A[mid] == x:
			result = mid
			high = mid - 1
		elif A[mid] < x:
			low = mid + 1
		else:
			high = mid - 1
	return result
