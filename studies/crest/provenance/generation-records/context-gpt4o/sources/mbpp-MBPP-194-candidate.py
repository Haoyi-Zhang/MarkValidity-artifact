def octal_To_Decimal(n):
	decimal_number = 0
	base = 1
	while 0 < n:
		last_digit = n % 10
		n = n // 10
		decimal_number += base * last_digit
		base = base * 8
	return decimal_number
