def binary_to_decimal(binary):
	binary_str = str(binary)
	return sum((2 ** i * int(digit) for i, digit in enumerate(reversed(binary_str))))
