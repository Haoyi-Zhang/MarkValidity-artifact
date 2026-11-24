def count_rotation(arr):   
	return next((i for i in range (1, len(arr)) if (arr[i - 1] > arr[i])), 0)
