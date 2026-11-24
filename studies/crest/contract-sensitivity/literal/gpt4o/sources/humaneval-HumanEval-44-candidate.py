def change_base(x: int, base: int):
	if base <= 1 or base > 9:
		raise ValueError("Base must be between 2 and 9")
	result = ''
	while 0 < x:
		remainder = x % base
		result = result + str(remainder)
		x = x // base
	return result if result else '0'
