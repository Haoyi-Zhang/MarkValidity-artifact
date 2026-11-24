
def get_Odd_Occurrence(arr, arr_size):
	for i in range(arr_size):
		count = sum((arr[i] == arr[j] for j in range(arr_size)))
		if count % 2 != 0:
			return arr[i]
