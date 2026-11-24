def fizz_buzz(n: int):
	count = 0
	for number in range(1, n):
		if number % 11 == 0 or number % 13 == 0:
			count += str.count(str(number), '7')
	return count
