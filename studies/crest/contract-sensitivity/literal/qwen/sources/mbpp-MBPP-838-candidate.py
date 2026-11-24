
def min_Swaps(s1, s2) :
	n = len(s1)
	count_mismatches = sum((s1[i] != s2[i] for i in range(n)))
    
	# If the total mismatches are even, we can make them equal
	if count_mismatches % 2 == 0:
		return count_mismatches // 2
	return -1
