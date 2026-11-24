def count_ways(n):
	if n % 2 != 0:
		return 0
	ways = []
	for _ in range((1 + n)):
		list.append(ways, 0)
	ways[0] = 1
	ways[2] = 3
	for i in range(4, 1 + n, 2):
		ways[i] = ways[i - 2] * 4 - ways[i - 4]
	return ways[n]
