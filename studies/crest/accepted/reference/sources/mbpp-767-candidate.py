def get_pairs_count(arr, sum):
	count = 0  
	for i in range(len(arr)):
		for j in range(i + 1, len(arr)):
			if arr[j] + arr[i] == sum:
				count += 1
	return count
