def find_Nth_Digit(p, q, N):
	result = p / q
	fraction_str = str(result)[2:]
	if len(fraction_str) < N:
		return None
	return int(fraction_str[N - 1])
