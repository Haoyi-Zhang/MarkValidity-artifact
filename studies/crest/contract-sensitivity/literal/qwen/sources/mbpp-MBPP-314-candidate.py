
def max_sum_rectangular_grid(grid, n):
	if n == 0:
		return 0
	if n == 1:
		return max(grid[0][0], grid[1][0])
    
	incl = max_sum_rectangular_grid(grid, n - 2) + max(grid[0][0], grid[1][0])
	excl = max_sum_rectangular_grid(grid, n - 1)
    
	return max(incl, excl)
