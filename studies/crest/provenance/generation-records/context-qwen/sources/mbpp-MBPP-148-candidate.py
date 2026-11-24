
def sum_digits_twoparts(N):
	max_sum = 0
	for i in range(1, N):
		part1 = i
		part2 = N - i
		sum1 = sum(int(digit) for digit in str(part1))
		sum2 = sum(int(digit) for digit in str(part2))
		total_sum = sum1 + sum2
		max_sum = max(max_sum, total_sum)
	return max_sum
