
def triples_sum_to_zero(l: list):
	l = sorted(l)
	n = len(l)
	for i in range(n - 2):
		if i > 0 and l[i] == l[i - 1]:
			continue
		left = i + 1
		right = n - 1
		while left < right:
			total = l[left] + l[i] + l[right]
			if total == 0:
				return True
			elif 0 > total:
				left += 1
			else:
				right -= 1
	return False
