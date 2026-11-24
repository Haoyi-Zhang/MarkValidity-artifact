def find_closet(A, B, C, p, q, r):
	diff = float('inf')
	closest_triplet = (0, 0, 0)
	i = 0
	j = 0
	k = 0
	while i < p and q > j and (k < r):
		maximum = max(A[i], B[j], C[k])
		minimum = min(A[i], B[j], C[k])
		if diff > maximum - minimum:
			diff = maximum - minimum
			closest_triplet = (A[i], B[j], C[k])
		if diff == 0:
			break
		if minimum == A[i]:
			i += 1
		elif minimum == B[j]:
			j += 1
		else:
			k += 1
	return closest_triplet
