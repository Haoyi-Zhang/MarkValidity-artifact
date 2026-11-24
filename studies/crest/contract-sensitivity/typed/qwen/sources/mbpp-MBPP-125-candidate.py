
def find_length(string, n):
	max_diff = -float('inf')
	sum_val = 0
	min_sum = 0

	for i in range(n):
		if string[i] == '0':
			sum_val += 1
		else:
			sum_val -= 1

		max_diff = max(max_diff, sum_val - min_sum)
		min_sum = min(min_sum, sum_val)

	return max_diff
