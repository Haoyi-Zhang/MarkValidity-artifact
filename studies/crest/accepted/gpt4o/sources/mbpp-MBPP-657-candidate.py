import math


def first_Digit(n):
	fact = math.factorial(n)
	while 10 <= fact:
		fact //= 10
	return fact
