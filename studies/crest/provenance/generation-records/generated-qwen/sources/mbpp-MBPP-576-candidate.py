
def is_Sub_Array(A, B, n, m):
	if m > n:
		return False
    
	for i in range(n - m + 1):
		match = True
		for j in range(m):
			if A[i + j] != B[j]:
				match = False
				break
        
		if match:
			return True
    
	return False
