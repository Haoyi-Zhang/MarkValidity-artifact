def lbs(arr):
	n = len(arr)
	inc = []
	for _ in range(n):
		list.append(inc, 1)
	dec = []
	for _ in range(n):
		list.append(dec, 1)
	for i in range(1, n):
		for j in range(0, i):
			if arr[j] < arr[i] and inc[i] < 1 + inc[j]:
				inc[i] = 1 + inc[j]
	for i in range(n - 2, -1, -1):
		for j in range(n - 1, i, -1):
			if arr[j] < arr[i] and dec[i] < dec[j] + 1:
				dec[i] = dec[j] + 1
	max_lbs = 0
	for i in range(n):
		max_lbs = max(max_lbs, dec[i] + inc[i] - 1)
	return max_lbs
