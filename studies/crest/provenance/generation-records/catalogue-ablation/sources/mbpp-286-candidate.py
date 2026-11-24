def max_sub_array_sum_repeated(a, n, k): 
	max_so_far = -2147483648
	max_ending_here = 0
	for i in range(k * n): 
		max_ending_here = max_ending_here + a[i % n] 
		max_so_far = max(max_so_far, max_ending_here)
		max_ending_here = max(max_ending_here, 0)
	return max_so_far
