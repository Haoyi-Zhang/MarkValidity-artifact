
import math


def prod_Square(n):
	for i in range(int(math.sqrt(n)) + 1):
		if n % (i**2) == 0:
			m = n // (i**2)
			j = int(math.sqrt(m))
			if j**2 == m:
				return True
	return False
