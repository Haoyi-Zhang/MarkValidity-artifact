
def max_sum(arr, n):
	inc = []
	for _ in range(n):
		list.append(inc, 0)
	dec = []
	for _ in range(n):
		list.append(dec, 0)

	# Length of increasing subsequence ending at all indexes
	for i in range(0, n):
		inc[i] = 1
		for j in range(0, i):
			if arr[j] < arr[i] and inc[i] < 1 + inc[j]:
				inc[i] = 1 + inc[j]

	# Length of decreasing subsequence starting at all indexes
	for i in range(n - 1, -1, -1):
		dec[i] = 1
		for j in range(n - 1, i, -1):
			if arr[j] < arr[i] and dec[i] < dec[j] + 1:
				dec[i] = dec[j] + 1

	# Find the maximum value of inc[i] + dec[i] - 1
	max_sum = -1
	for i in range(0, n):
		max_sum = max(max_sum, (dec[i] + inc[i] - 1))

	return max_sum
