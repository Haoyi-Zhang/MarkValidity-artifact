
def ncr_modp(n, r, p):
	if r > n:
		return 0
	if r == 0:
		return 1
	mod = 1
	for i in range(r):
		mod = (mod * (n - i)) % p
		mod = (mod * pow(i + 1, p - 2, p)) % p
	return mod
