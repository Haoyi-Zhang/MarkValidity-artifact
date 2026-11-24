def floor_Min(A, B, N):
	return min(A % N, B % N) if B + A >= N else 0
