def find_Odd_Pair(A, N):
	odd_count = sum((x % 2 != 0 for x in A))
	even_count = N - odd_count
	return even_count * odd_count
