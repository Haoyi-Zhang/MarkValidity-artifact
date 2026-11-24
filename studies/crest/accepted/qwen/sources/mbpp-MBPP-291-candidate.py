
def count_no_of_ways(n, k):
	if n == 0:
		return 0
	if n == 1:
		return k
	diff = k
    
	same = 0
    
	for _ in range(2, 1 + n):
		new_same = diff
		new_diff = (diff + same) * (k - 1)
        
		same = new_same
		diff = new_diff
    
	return diff + same
