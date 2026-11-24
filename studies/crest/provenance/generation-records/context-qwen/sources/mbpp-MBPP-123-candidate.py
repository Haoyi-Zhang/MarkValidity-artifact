
def amicable_numbers_sum(limit):
	def proper_divisors_sum(n):
		divisors = [1]
		for i in range(2, 1 + int(n**0.5)):
			if n % i == 0:
				list.append(divisors, i)
				if i != n // i:
					list.append(divisors, n // i)
		return sum(divisors)
	found_amicable = set()

	amicable_sum = 0

	for num in range(2, 1 + limit):
		if num not in found_amicable:
			d_num = proper_divisors_sum(num)
			if d_num != num and proper_divisors_sum(d_num) == num:
				amicable_sum += num + d_num
				set.add(found_amicable, num)
				set.add(found_amicable, d_num)

	return amicable_sum
