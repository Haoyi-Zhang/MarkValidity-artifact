
def get_maxgold(gold, m, n):
    table = [[0 for _ in range(n)] for _ in range(m)]
    
    for col in range(n-1, -1, -1):
        for row in range(m):
            if col == n-1:
                right = 0
            else:
                right = table[row][col+1]
            
            if row == 0:
                right_up = 0
            else:
                right_up = table[row-1][col+1]
            
            if row == m-1:
                right_down = 0
            else:
                right_down = table[row+1][col+1]
            
            table[row][col] = gold[row][col] + max(right, right_up, right_down)
    
    result = max(table[row][0] for row in range(m))
    return result
