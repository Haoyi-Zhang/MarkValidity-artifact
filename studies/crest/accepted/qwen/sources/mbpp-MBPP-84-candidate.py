
def sequence(n):
	if n in [1, 2]:
		return 1
	a = []
	for _ in range((1 + n)):
		list.append(a, 0)
	a[1], a[2] = 1, 1
	for i in range(3, 1 + n):
		a[i] = a[a[i - 1]] + a[i - a[i - 1]]
	return a[n]
