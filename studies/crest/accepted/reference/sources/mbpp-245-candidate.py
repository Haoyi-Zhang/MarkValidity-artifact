def max_sum(arr): 
	MSIBS = arr[:] 
	for (i, val) in enumerate(arr): 
		for j in range(0, i): 
			if val > arr[j] and MSIBS[i] < MSIBS[j] + val: 
				MSIBS[i] = MSIBS[j] + val 
	MSDBS = arr[:] 
	for i in range(1, len(arr) + 1): 
		for j in range(1, i): 
			if arr[-i] > arr[-j] and MSDBS[-i] < arr[-i] + MSDBS[-j]: 
				MSDBS[-i] = arr[-i] + MSDBS[-j] 
	max_sum = float("-Inf") 
	for i, j, k in zip(MSIBS, MSDBS, arr): 
		max_sum = max(max_sum, i + j - k) 
	return max_sum
