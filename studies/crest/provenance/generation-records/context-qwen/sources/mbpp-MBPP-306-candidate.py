
def max_sum_increasing_subseq(a, n, index, k):
	if index >= n:
		return 0
	if k < index:
		return max_sum_increasing_subseq(a, n, 1 + index, k)
	incl = a[index] + max_sum_increasing_subseq(a, n, 1 + index, n) if (k == n or a[index] < a[k]) else float('-inf')
	excl = max_sum_increasing_subseq(a, n, 1 + index, k)
	return max(incl, excl)

