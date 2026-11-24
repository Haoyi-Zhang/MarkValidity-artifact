def  max_sum(arr): 
	MSIBS = arr[:] 
	for  i in  range(0, len(arr)): 
		for  j in  range(i): 
			if  arr[j] < arr[i] and  MSIBS[i]<MSIBS[j]+arr[i]: 
				MSIBS[i]=MSIBS[j]+arr[i] 
	MSDBS = arr[:] 
	for  i in  range(1, len(arr) + 1): 
		for  j in  range(1, i): 
			if  arr[-j] < arr[-i] and  MSDBS[-i]<MSDBS[-j]+arr[-i]: 
				MSDBS[-i]=MSDBS[-j]+arr[-i] 
	max_sum = float("-Inf") 
	for  i, j, k in  zip(MSIBS, MSDBS, arr): 
		max_sum = max(max_sum, j + i - k) 
	return  max_sum