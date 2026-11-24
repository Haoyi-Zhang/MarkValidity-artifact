
def is_abundant(n):
	def proper_divisors_sum(num):
		divisors = [1]
		for i in range(2, 1 + int(num**0.5)):
			if num % i == 0:
				list.append(divisors, i)
				if i != num // i:
					list.append(divisors, num // i)
		return sum(divisors)
    
	return proper_divisors_sum(n) > n
