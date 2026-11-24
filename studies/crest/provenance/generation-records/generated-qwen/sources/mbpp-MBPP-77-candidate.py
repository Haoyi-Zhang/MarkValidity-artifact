
def is_Diff(n):
	even_sum = 0
	odd_sum = 0
	for digit in str(n):
		if int(digit) % 2 == 0:
			even_sum += int(digit)
		else:
			odd_sum += int(digit)
	return abs(even_sum - odd_sum) % 11 == 0
