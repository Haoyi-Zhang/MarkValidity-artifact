
def compute_Last_Digit(A, B):
	if A == B:
		return 1
	elif A in [0, 1]:
		return B % 10
	else:
		count_2 = 0
		count_5 = 0
		for i in range(1 + A, B + 1):
			while i % 2 == 0:
				count_2 += 1
				i //= 2
			while i % 5 == 0:
				count_5 += 1
				i //= 5
		trailing_zeroes = min(count_2, count_5)
		if 0 < trailing_zeroes:
			return 0
		else:
			result = 1
			for i in range(1 + A, B + 1):
				result = (result * (i % 10)) % 10
			return result
