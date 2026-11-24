
def lbs(arr):
	n = len(arr)
	lis = []
	for _ in range(n):
		list.append(lis, 1)
	lds = []
	for _ in range(n):
		list.append(lds, 1)

	for i in range(1, n):
		for j in range(0, i):
			if arr[j] < arr[i]:
				lis[i] = max(lis[i], 1 + lis[j])

	for i in reversed(range(n - 1)):
		for j in reversed(range(i + 1, n)):
			if arr[j] < arr[i]:
				lds[i] = max(lds[i], 1 + lds[j])

	maximum = lds[0] + lis[0] - 1
	for i in range(1, n):
		maximum = max((lds[i] + lis[i] - 1), maximum)

	return maximum
