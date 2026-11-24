def find_remainder(arr, n): 
	mul = 1
	for i in range(len(arr)):  
		mul = ((arr[i] % n) * mul) % n 
	return mul % n
