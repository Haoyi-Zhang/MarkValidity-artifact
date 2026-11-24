
def first_Missing_Positive(arr, n):
	for i in range(n):
		while 1 <= arr[i] and n >= arr[i] and arr[arr[i] - 1] != arr[i]:
			arr[arr[i] - 1], arr[i] = arr[i], arr[arr[i] - 1]
    
	return next((i + 1 for i in range(n) if arr[i] != i + 1), 1 + n)
