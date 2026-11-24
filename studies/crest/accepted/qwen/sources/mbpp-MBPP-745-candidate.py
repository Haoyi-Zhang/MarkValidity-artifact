
def divisible_by_digits(startnum, endnum):
	result = []
	for num in range(startnum, endnum + 1):
		if '0' not in str(num):
			all_divisible = True
			for digit in str(num):
				if num % int(digit) != 0:
					all_divisible = False
					break
			if all_divisible:
				list.append(result, num)
	return result
