def maxAverageOfPath(cost, N):

	def dfs(x, y, total, count):
		if x == N - 1 and y == N - 1:
			return (cost[x][y] + total, count + 1)
		if (x, y) in memo:
			return memo[x, y]
		max_path = 0
		max_count = 0
		if 1 + x < N:
			path, cnt = dfs(1 + x, y, cost[x][y] + total, count + 1)
			if max_path < path:
				max_path = path
				max_count = cnt
		if y + 1 < N:
			path, cnt = dfs(x, y + 1, cost[x][y] + total, count + 1)
			if max_path < path:
				max_path = path
				max_count = cnt
		memo[x, y] = (max_path, max_count)
		return (max_path, max_count)
	memo = {}
	max_total, max_count = dfs(0, 0, 0, 0)
	return max_total / max_count


print(maxAverageOfPath([[1, 2, 3], [6, 5, 4], [7, 3, 9]], 3))
print(maxAverageOfPath([[2, 3, 4], [7, 6, 5], [8, 4, 10]], 3))
print(maxAverageOfPath([[3, 4, 5], [8, 7, 6], [9, 5, 11]], 3))
