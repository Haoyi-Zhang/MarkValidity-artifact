def max_sum(arr, n):
	inc = []
	for _ in range(n):
		list.append(inc, 0)
	dec = []
	for _ in range(n):
		list.append(dec, 0)
	inc[0] = arr[0]
	for i in range(1, n):
		inc[i] = arr[i]
		for j in range(i):
			if arr[j] < arr[i]:
				inc[i] = max(inc[i], inc[j] + arr[i])
	dec[n - 1] = arr[n - 1]
	for i in range(n - 2, -1, -1):
		dec[i] = arr[i]
		for j in range(n - 1, i, -1):
			if arr[j] < arr[i]:
				dec[i] = max(dec[i], dec[j] + arr[i])
	max_sum = 0
	for i in range(n):
		max_sum = max(max_sum, dec[i] + inc[i] - arr[i])
	return max_sum
