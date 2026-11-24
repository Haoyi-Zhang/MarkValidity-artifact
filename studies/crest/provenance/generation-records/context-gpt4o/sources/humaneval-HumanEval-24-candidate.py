def largest_divisor(n: int) -> int:
	return next((i for i in range(n // 2, 0, -1) if n % i == 0), None)
