def is_Sub_Array(A, B, n, m):
	if m > n:
		return False
	if any((A[i:i + m] == B for i in range(n - m + 1))):
		return True
	return False
