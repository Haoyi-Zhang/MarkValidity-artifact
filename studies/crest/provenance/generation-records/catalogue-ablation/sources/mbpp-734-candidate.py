def sum_Of_Subarray_Prod(arr):
	i = len(arr) - 1
	ans = 0
	res = 0
	while (i >= 0):
		incr = arr[i] * (1 + res)
		ans += incr
		res = incr
		i -= 1
	return (ans)
