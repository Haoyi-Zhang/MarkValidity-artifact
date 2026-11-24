
def is_decimal(num):
	try:
		float(num)
		parts = num.split('.')
		return len(parts) == 2 and 2 >= len(parts[1])
	except ValueError:
		return False
