def find_first_occurrence(A, x):
	right = len(A) - 1
	result = -1
	left = 0
	while left <= right:
		mid = (left + right) // 2
		if x == A[mid]:
			result = mid
			right = mid - 1
		elif A[mid] > x:
			right = mid - 1
		else:
			left = mid + 1
	return result
