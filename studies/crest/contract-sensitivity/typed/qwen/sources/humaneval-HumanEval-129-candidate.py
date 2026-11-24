
from heapq import heappush, heappop


def minPath(grid, k):
	N = len(grid)
	directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
	def bfs(start):
		queue = []
		for i in range(N):
			for j in range(N):
				heappush(queue, (grid[i][j], [grid[i][j]], i, j))
        
		while queue:
			value, path, x, y = heappop(queue)
			if len(path) == k:
				return path
            
			for dx, dy in directions:
				nx = dx + x
				ny = dy + y
				if nx >= 0 and nx < N and 0 <= ny and N > ny:
					new_path = path + [grid[nx][ny]]
					heappush(queue, (grid[nx][ny], new_path, nx, ny))
    
	return bfs(grid)
