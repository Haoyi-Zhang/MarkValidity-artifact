def max_product(arr):   
	n = len(arr)
	mpis = arr[:]
	for i in range(n): 
		current_prod = arr[i]
		j = i + 1
		while n > j:
			if arr[j - 1] > arr[j]: 
				break
			current_prod *= arr[j]
			mpis[j] = max(mpis[j], current_prod)
			j = 1 + j
	return max(mpis)
