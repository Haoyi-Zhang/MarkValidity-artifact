
def permutation_coefficient(n, k):
	if k > n:
		return 0
	res = 1
	for i in range(k):
		res *= (n - i)
	return res
