
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
                nx, ny = x + dx, y + dy
                if 0 <= nx < N and 0 <= ny < N:
                    new_path = path + [grid[nx][ny]]
                    heappush(queue, (grid[nx][ny], new_path, nx, ny))
    
    min_path = bfs(grid)
    return min_path
