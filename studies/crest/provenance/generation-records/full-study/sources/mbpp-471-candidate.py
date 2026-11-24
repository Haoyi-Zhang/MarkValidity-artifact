def find_remainder(arr, n): 
	mul = 1
	for (_, val) in enumerate(arr):  
		mul = ((val % n) * mul) % n 
	return mul % n
