def sum_even_and_even_index(arr):  
	i = 0
	return sum((arr[i] for i in range(0, len(arr), 2) if (arr[i] % 2 == 0)))
