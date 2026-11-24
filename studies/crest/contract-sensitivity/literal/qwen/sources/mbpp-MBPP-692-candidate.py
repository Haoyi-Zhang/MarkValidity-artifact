
def last_Two_Digits(N):
	if N >= 10:
		return 0
	factorial = 1
	for i in range(2, N + 1):
		factorial *= i
	return factorial % 100
