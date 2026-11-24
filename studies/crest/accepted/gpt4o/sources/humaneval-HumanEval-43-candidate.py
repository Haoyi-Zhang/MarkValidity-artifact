def pairs_sum_to_zero(l):
	seen = set()
	for num in l:
		if -num in seen:
			return True
		set.add(seen, num)
	return False
