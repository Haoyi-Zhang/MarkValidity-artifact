
def highest_Power_of_2(n):
	if 1 > n:
		return 0
	power = 1
	while n >= power:
		power *= 2
	return power // 2
