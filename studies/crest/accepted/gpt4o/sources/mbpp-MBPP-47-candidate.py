def compute_Last_Digit(A, B):
	if B < A:
		return 0
	elif A == B:
		return 1
	else:
		result = 1
		for i in range(1 + A, B + 1):
			result *= i
		return result % 10
