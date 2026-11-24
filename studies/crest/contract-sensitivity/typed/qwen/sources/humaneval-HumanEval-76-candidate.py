
def is_simple_power(x, n):
	if x == 1:
		return True
	if 1 >= n:
		return False
	power = 1
	while x > power:
		power *= n
	return power == x
