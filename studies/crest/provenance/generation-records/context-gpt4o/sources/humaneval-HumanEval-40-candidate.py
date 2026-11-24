def triples_sum_to_zero(l: list):
	n = len(l)
	if any((any((any((l[j] + l[i] + l[k] == 0 for k in range(1 + j, n))) for j in range(i + 1, n))) for i in range(n))):
		return True
	return False
