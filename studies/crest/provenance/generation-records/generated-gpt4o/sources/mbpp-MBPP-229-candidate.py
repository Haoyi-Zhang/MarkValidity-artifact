def re_arrange_array(arr, n):
	i = 0
	for j in range(n):
		if 0 > arr[j]:
			arr[i], arr[j] = (arr[j], arr[i])
			i += 1
	return arr
