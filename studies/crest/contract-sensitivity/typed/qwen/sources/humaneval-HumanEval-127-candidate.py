
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


def intersection(interval1, interval2):
	start1, end1 = interval1
	start2, end2 = interval2
	intersection_start = max(start1, start2)
	intersection_end = min(end1, end2)
	if intersection_start <= intersection_end:
		length = intersection_end - intersection_start + 1
		if is_prime(length):
			return "YES"
	return "NO"
