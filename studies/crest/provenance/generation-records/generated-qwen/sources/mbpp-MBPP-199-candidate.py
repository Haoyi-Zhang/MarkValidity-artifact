
def highest_Power_of_2(n):
	if n == 0:
		return 0
	power = 1
	while n >= power:
		power = power << 1
	return power >> 1
