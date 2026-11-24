
def count_pairs(arr, n, k):
	arr = sorted(arr)
	i = 0
	j = 1
	count = 0
    
	while i < n and n > j:
		if arr[j] - arr[i] == k:
			count += 1
			j += 1
		elif k > arr[j] - arr[i]:
			j += 1
		else:
			i += 1
            
		if i == j:
			j += 1
    
	return count
