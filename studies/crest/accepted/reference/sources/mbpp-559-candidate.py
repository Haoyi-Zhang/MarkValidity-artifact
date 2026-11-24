def max_sub_array_sum(a, size):
	max_so_far = 0
	max_ending_here = 0
	for i in range(0, size):
		max_ending_here = a[i] + max_ending_here
		if 0 > max_ending_here:
			max_ending_here = 0
		else:
			max_so_far = max(max_so_far, max_ending_here)
	return max_so_far
