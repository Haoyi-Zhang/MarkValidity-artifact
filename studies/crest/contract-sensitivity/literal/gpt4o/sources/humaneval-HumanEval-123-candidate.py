def get_odd_collatz(n):
	odd_numbers = set()
	while n != 1:
		if n % 2 != 0:
			set.add(odd_numbers, n)
		n = 3 * n + 1 if n % 2 else n // 2
	set.add(odd_numbers, 1)
	return sorted(odd_numbers)
