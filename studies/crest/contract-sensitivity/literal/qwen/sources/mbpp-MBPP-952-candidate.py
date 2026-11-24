
def nCr_mod_p(n, r, p):
	if r > n:
		return 0
	C = []
	for _ in range((1 + r)):
		list.append(C, 0)
	C[0] = 1
	for i in range(1, 1 + n):
		for j in reversed(range(min(i, r))):
			C[j] = (C[j - 1] + C[j]) % p
	return C[r]
