def hex_key(num):
	prime_hex_digits = {'2', '3', '5', '7', 'B', 'D'}
	return sum(digit in prime_hex_digits for digit in num)
