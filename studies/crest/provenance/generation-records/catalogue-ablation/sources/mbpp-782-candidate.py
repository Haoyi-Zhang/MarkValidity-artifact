def odd_length_sum(arr):
	l = len(arr)
	Sum = 0
	for i in range(l):
		Sum += ((((i + 1) * (l - i) + 1) // 2) * arr[i])
	return Sum
