
def floor_Max(A, B, N):
	if B <= A:
		return N - (N // A) * A
	return B * (N // A)
