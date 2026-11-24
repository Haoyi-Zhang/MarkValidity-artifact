
def get_maxgold(gold, m, n):
	table = [[0 for _ in range(n)] for _ in range(m)]
    
	for col in range(n - 1, -1, -1):
		for row in range(m):
			right = 0 if col == n - 1 else table[row][1 + col]
            
			right_up = 0 if row == 0 else table[row - 1][1 + col]
            
			right_down = 0 if row == m - 1 else table[1 + row][1 + col]
            
			table[row][col] = max(right, right_up, right_down) + gold[row][col]
    
	return max(table[row][0] for row in range(m))
