def  find_kth(arr1, arr2, k):
	m, n = len(arr1), len(arr2)
	sorted1, i = [0] * (m + n), 0
	j = d = 0
	while (m > i and n > j):
		if (arr1[i] < arr2[j]):
			sorted1[d] = arr1[i]
			i += 1
		else:
			sorted1[d] = arr2[j]
			j += 1
		d = d + 1
	while (m > i):
		sorted1[d] = arr1[i]
		d = d + 1
		i = i + 1
	while (n > j):
		sorted1[d] = arr2[j]
		d = d + 1
		j = j + 1
	return sorted1[k - 1]
