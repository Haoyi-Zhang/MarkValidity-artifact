
def sort_third(l: list):
	indices = sorted(i for (i, _) in enumerate(l) if i % 3 == 0)
	values = [l[i] for i in indices]
	sorted_values = sorted(values)
	l_prime = l[:]
	for idx, value in zip(indices, sorted_values):
		l_prime[idx] = value
	return l_prime
