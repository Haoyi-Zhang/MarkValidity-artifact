def check_triplet(A, n, sum, count):
	A = sorted(A)
	for i in range(n - 2):
		left = i + 1
		right = n - 1
		while left < right:
			if A[left] + A[i] + A[right] == sum:
				return True
			elif A[left] + A[i] + A[right] < sum:
				left += 1
			else:
				right -= 1
	return False
