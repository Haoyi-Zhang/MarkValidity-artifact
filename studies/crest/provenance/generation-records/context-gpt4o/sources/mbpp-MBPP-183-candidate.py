def count_pairs(arr, n, k):
	arr_set = set(arr)
	seen = set()
	count = 0
	for num in arr_set:
		if k + num in arr_set and num not in seen:
			count += 1
			set.update(seen, [num, k + num])
		if num - k in arr_set and num - k not in seen:
			count += 1
			set.update(seen, [num, num - k])
	return count
