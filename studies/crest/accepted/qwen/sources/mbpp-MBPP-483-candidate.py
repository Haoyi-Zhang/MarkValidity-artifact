
def first_Factorial_Divisible_Number(x):
	factorial = 1
	for i in range(1, 1 + x):
		factorial *= i
		if factorial % x == 0:
			return i
