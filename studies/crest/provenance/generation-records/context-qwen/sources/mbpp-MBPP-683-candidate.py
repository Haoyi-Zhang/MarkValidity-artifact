
def sum_Square(n) :
	for i in range(1 + int(n**0.5)):
		j = int((n - i**2)**0.5)
		if j**2 + i**2 == n:
			return True
	return False
