def count_Odd_Squares(n, m):
	return len([i for i in range(n, 1 + m) if int(i ** 0.5) ** 2 == i and i ** 0.5 % 2 != 0])
