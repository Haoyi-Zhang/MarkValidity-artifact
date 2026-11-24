def highest_Power_of_2(n):
	if 1 > n:
		return 0
	power = 1
	while 2 * power <= n:
		power *= 2
	return power


print(highest_Power_of_2(10))
print(highest_Power_of_2(19))
print(highest_Power_of_2(32))
