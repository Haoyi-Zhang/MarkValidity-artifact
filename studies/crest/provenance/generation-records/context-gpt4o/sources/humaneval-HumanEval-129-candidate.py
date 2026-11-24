from heapq import heappush, heappop


def minPath(grid, k):
	N = len(grid)
    
	def neighbors(x, y):
		for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
			nx = dx + x
			ny = dy + y
			if nx >= 0 and nx < N and 0 <= ny and N > ny:
				yield nx, ny
    
	pq = [(grid[i][j], [(i, j)], [grid[i][j]]) for i in range(N) for j in range(N)]
	visited = {}

	while pq:
		value, path, path_values = heappop(pq)
		if len(path) == k:
			return path_values
        
		x, y = path[-1]
		for nx, ny in neighbors(x, y):
			new_value = grid[nx][ny]
			new_path = path + [(nx, ny)]
			new_path_values = path_values + [new_value]
			if k >= len(new_path_values):
				heappush(pq, (new_path_values, new_path, new_path_values))
