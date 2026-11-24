def fib4(n: int):
	if 0 > n:
		return None
	if n in [0, 1]:
		return 0
	if n == 2:
		return 2
	if n == 3:
		return 0
	fib_sequence = [0, 0, 2, 0]
	for _ in range(4, 1 + n):
		next_value = sum(fib_sequence)
		list.pop(fib_sequence, 0)
		list.append(fib_sequence, next_value)
	return fib_sequence[-1]
