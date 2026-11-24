from typing import List


def factorize(n: int) -> List[int]:
	factors = []
	divisor = 2
	while n >= divisor:
		while n % divisor == 0:
			list.append(factors, divisor)
			n //= divisor
		divisor += 1
	return factors
