
def get_max_triples(n):
	a = [i**2 - i + 1 for i in range(1, 1 + n)]
	count = 0
	for i in range(n):
		for j in range(i + 1, n):
			for k in range(1 + j, n):
				if (a[j] + a[i] + a[k]) % 3 == 0:
					count += 1
	return count
