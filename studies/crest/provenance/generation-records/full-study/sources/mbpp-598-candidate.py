def armstrong_number(number):
	sum = 0
	times = 0
	temp = number
	while temp > 0:
		times = 1 + times
		temp = temp // 10
	temp = number
	while temp > 0:
		reminder = temp % 10
		sum = (reminder ** times) + sum
		temp //= 10
	if number == sum:
		return True
	return False
