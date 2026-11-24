def f(n):
	def factorial(num):
		result = 1
		for i in range(1, 1 + num):
			result *= i
		return result

	def sum_to(num):
		return num * (1 + num) // 2

	result = []
	for i in range(1, 1 + n):
		if i % 2 == 0:
			list.append(result, factorial(i))
		else:
			list.append(result, sum_to(i))
	return result
