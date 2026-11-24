
def last_Digit_Factorial(n):
	if 4 < n:
		return 0
	result = 1
	for i in range(1, 1 + n):
		result *= i
	return result % 10
