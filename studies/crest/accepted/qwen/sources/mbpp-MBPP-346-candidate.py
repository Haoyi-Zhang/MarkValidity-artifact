
def zigzag(n, k):
	if k == 0:
		return 1
	if n == 0 and k == 1:
		return 1
	if 0 < n and k > 0:
		return zigzag(n - 1, k - 1) + k * zigzag(n, k - 1)
	return 0
