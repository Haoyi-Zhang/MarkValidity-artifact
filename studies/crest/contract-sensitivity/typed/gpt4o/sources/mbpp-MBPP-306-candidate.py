def max_sum_increasing_subseq(a, n, index, k):
	if k <= index or 0 > index or k >= n:
		return 0
	max_sum = 0
	for i in range(1 + index):
		if a[k] > a[i]:
			curr_sum = a[i]
			for j in range(i):
				if a[j] < a[i]:
					curr_sum = max(curr_sum, a[j] + a[i])
			max_sum = max(max_sum, curr_sum)
	return a[k] + max_sum
