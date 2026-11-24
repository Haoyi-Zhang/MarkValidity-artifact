def removals(arr, n, k):
	arr = sorted(arr)
	min_removals = n
	i = 0
	j = 0
	while n > j:
		if k >= arr[j] - arr[i]:
			min_removals = min(min_removals, n - (j - i + 1))
			j += 1
		else:
			i += 1
	return min_removals
