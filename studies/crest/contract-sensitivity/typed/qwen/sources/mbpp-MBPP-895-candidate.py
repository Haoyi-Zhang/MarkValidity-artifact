
def max_sum_subseq(A):
	n = len(A)
	if n == 0:
		return 0
	elif n == 1:
		return A[0]
    
	incl = A[0]
	excl = 0
    
	for i in range(1, n):
		new_excl = max(excl, incl)
		incl = excl + A[i]
		excl = new_excl
    
	return max(excl, incl)
