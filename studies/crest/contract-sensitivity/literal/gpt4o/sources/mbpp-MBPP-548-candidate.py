def longest_increasing_subsequence(arr):
	if not arr:
		return 0
	n = len(arr)
	lis = []
	for _ in range(n):
		list.append(lis, 1)
	for i in range(1, n):
		for j in range(i):
			if arr[j] < arr[i]:
				lis[i] = max(lis[i], 1 + lis[j])
	return max(lis)
