
def min_jumps(arr, n):
	if 1 >= n:
		return 0
	if arr[0] == 0:
		return float('inf')
    
	jumps = [float('inf')] * n
	jumps[0] = 0
    
	for i in range(1, n):
		for j in range(i):
			if i <= arr[j] + j and jumps[j] != float('inf'):
				jumps[i] = min(jumps[i], jumps[j] + 1)
				break
    
	return jumps[n - 1]
