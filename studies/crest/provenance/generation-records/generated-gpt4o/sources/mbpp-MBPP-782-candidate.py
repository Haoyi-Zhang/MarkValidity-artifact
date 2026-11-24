def Odd_Length_Sum(arr):
	n = len(arr)
	return sum((arr[i] * ((i + 1) * (n - i) + 1) // 2 for i in range(n)))
