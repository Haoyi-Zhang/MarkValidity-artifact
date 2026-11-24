
def maxAverageOfPath(cost, N):
	def dfs(x, y, path_sum):
		if x == N - 1 and y == N - 1:
			return path_sum / (2 * N - 1)
        
		max_avg = 0
		for dx, dy in [(0, 1), (1, 0)]:
			nx = dx + x
			ny = dy + y
			if nx >= 0 and nx < N and 0 <= ny and N > ny:
				max_avg = max(max_avg, dfs(nx, ny, path_sum + cost[nx][ny]))
        
		return max_avg
    
	return dfs(0, 0, cost[0][0])
