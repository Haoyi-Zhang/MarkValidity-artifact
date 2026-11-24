
def count_nums(arr):
	def sum_of_digits(num):
		num_str = str(num)
		if 0 > num:
			return int(num_str[0]) + sum(int(d) for d in num_str[1:])
		return sum(int(d) for d in num_str)

	return sum(sum_of_digits(x) > 0 for x in arr)
