def max_sum_pair_diff_lessthan_K(arr, N, K):
	arr = sorted(arr, reverse=True)
	used = []
	for _ in range(N):
		list.append(used, False)
	result = 0
	for i in range(N):
		if used[i]:
			continue
		for j in range(i + 1, N):
			if not used[j] and K > abs(arr[i] - arr[j]):
				result += arr[j] + arr[i]
				used[i] = True
				used[j] = True
				break
	return result
