
def decimal_to_binary(n):
	if n == 0:
		return '0'
	binary = ''
	while 0 < n:
		binary = str(n % 2) + binary
		n = n // 2
	return binary
