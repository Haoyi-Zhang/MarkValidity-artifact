def max_subarray_product(arr):
	max_ending_here = arr[0]
	min_ending_here = arr[0]
	max_so_far = arr[0]
	for num in arr[1:]:
		temp_max = max(num, num * max_ending_here, min_ending_here * num)
		min_ending_here = min(num, num * max_ending_here, min_ending_here * num)
		max_ending_here = temp_max
		max_so_far = max(max_so_far, max_ending_here)
	return max_so_far
