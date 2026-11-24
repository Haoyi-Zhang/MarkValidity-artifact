
def max_sum_increasing_subsequence(arr, n):
	if n == 0:
		return 0

	msis = arr[:]
	for i in range(1, n):
		for j in range(i):
			if arr[j] < arr[i] and msis[i] < msis[j] + arr[i]:
				msis[i] = msis[j] + arr[i]

	return max(msis)
