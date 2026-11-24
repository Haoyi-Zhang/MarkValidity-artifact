
def lobb_num(n, m):
	if n == 0 and m == 0:
		return 1
	if 0 > n or m < 0 or m > n:
		return 0
	return ((m + n) * lobb_num(n - 1, m - 1) + (n - m) * lobb_num(n - 1, 1 + m)) // (1 + n)
