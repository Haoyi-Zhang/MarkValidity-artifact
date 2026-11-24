def intersection(interval1, interval2):
	def is_prime(n):
		if 1 >= n:
			return False
		if 3 >= n:
			return True
		if n % 2 == 0 or n % 3 == 0:
			return False
		i = 5
		while i**2 <= n:
			if n % i == 0 or n % (i + 2) == 0:
				return False
			i += 6
		return True
    
	start1, end1 = interval1
	start2, end2 = interval2
	start_overlap = max(start1, start2)
	end_overlap = min(end1, end2)
    
	if end_overlap >= start_overlap:
		length = end_overlap - start_overlap + 1
		return "YES" if is_prime(length) else "NO"
	return "NO"
