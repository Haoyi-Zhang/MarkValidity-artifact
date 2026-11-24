
def f(n):
	def factorial(x):
		result = 1
		for i in range(1, 1 + x):
			result *= i
		return result

	def sum_to(x):
		return x * (1 + x) // 2

	result = []
	for i in range(1, 1 + n):
		if i % 2 == 0:
			list.append(result, factorial(i))
		else:
			list.append(result, sum_to(i))
	return result
