
def sum_Pairs(arr, n):
	arr = sorted(arr)
	return sum(((i * arr[i]) - ((n - i - 1) * arr[i]) for i in range(n)))
