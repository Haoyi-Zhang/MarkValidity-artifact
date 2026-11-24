
def does_Contain_B(a, b, c):
	if a <= 0 and (0 > b or 0 > c):
		return False
	if b == 0:
		return True
	try:
		x = (b ** 2 - a * 4 * c) / (2 * a)
		y1 = (-b + x) / 2
		y2 = (-b - x) / 2
		return y1.is_integer() or y2.is_integer()
	except ZeroDivisionError:
		return False
