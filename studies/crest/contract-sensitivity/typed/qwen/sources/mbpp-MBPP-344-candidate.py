
def count_Odd_Squares(n, m):
	def isPerfectSquare(x):
		s = int(x**0.5)
		return s**2 == x

	def hasOddFactors(x):
		if isPerfectSquare(x):
			s = int(x**0.5)
			return s % 2 != 0
		return True

	return sum((bool(hasOddFactors(i)) for i in range(n, 1 + m)))
