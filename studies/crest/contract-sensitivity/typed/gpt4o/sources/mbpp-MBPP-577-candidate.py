def last_Digit_Factorial(n):
	if 5 <= n:
		return 0
	factorial = 1
	for i in range(2, 1 + n):
		factorial *= i
	return factorial % 10
