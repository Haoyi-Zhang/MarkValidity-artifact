def find_Max_Num(arr) : 
	n = len(arr)
	arr = sorted(arr, reverse=True) 
	num = arr[0] 
	for i in range(1, n) : 
		num = 10 * num + arr[i] 
	return num
