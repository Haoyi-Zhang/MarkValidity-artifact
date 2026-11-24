
def Sum_of_Inverse_Divisors(N, Sum):
	return sum((1 / i for i in range(1, N + 1) if Sum % i == 0))
