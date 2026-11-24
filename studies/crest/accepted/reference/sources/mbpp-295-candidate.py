def sum_div(number):
	divisors = [1]
	list.extend(divisors, (i for i in range(2, number) if (number % i) == 0))
	return sum(divisors)
