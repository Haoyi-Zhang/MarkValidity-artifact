
def sumOfEvenFactors(n):
	res = 1
	if n % 2 == 0:
		while n % 2 == 0:
			n //= 2
		for i in range(3, 1 + int(n**0.5), 2):
			factorCount = 0
			currentSum = 1
			currentTerm = 1
			while n % i == 0:
				factorCount += 1
				n //= i
				currentTerm *= i
				currentSum += currentTerm
			res *= currentSum
		if 2 <= n:
			res *= (1 + n)
	return 2 * res
