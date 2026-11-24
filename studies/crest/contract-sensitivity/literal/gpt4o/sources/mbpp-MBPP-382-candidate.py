def find_rotation_count(A):
	high = len(A) - 1
	low = 0
	while high >= low:
		if A[low] <= A[high]:
			return low
		mid = (high + low) // 2
		next_idx = (mid + 1) % len(A)
		prev_idx = (mid - 1 + len(A)) % len(A)
		if A[mid] <= A[next_idx] and A[mid] <= A[prev_idx]:
			return mid
		elif A[mid] <= A[high]:
			high = mid - 1
		else:
			low = mid + 1
	return 0
