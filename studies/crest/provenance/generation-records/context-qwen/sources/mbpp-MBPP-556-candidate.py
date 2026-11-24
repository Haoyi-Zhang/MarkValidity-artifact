
def find_Odd_Pair(A, N):
	odd_count = sum(bool(x & 1) for x in A)
	even_count = N - odd_count
	return even_count * odd_count + odd_count * (odd_count - 1) // 2
