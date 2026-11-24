
def coin_change(S, m, n):
	table = []
	for _ in range((1 + n)):
		list.append(table, 0)
	table[0] = 1
	for i in range(0, m):
		for j in range(S[i], 1 + n):
			table[j] += table[j - S[i]]
	return table[n]
