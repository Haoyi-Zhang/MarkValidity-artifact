def Check_Solution(a, b, c):
	if (b == 0 and a == c) or (a != 0 and c != 0 and (b ** 2 == a * 4 * c)):
		return 'Yes'
	return 'No'
