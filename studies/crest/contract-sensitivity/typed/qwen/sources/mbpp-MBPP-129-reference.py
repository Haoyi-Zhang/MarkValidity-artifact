
    n = len(my_matrix)
    if n == 0:
        return False
    
    # Calculate the sum of the first row to use as a reference
    magic_sum = sum(my_matrix[0])
    
    # Check rows
    for row in my_matrix:
        if sum(row) != magic_sum:
            return False
    
    # Check columns
    for col in range(n):
        if sum(my_matrix[row][col] for row in range(n)) != magic_sum:
            return False
    
    # Check diagonals
    if sum(my_matrix[i][i] for i in range(n)) != magic_sum:
        return False
    if sum(my_matrix[i][n-1-i] for i in range(n)) != magic_sum:
        return False
    
    return True
