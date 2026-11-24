def find_Points(l1, r1, l2, r2):
	if l2 > r1 or r2 < l1 or l2 > l1:
		return (l1, r2)
	return (l2, r1)
