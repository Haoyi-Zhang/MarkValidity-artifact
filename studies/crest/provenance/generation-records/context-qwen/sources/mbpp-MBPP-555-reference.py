
def difference(n):
    def sum_of_squares(x):
        return sum(i**3 for i in range(1, x + 1))
    
    def sum_of_numbers(x):
        return sum(i for i in range(1, x + 1))
    
    return sum_of_squares(n) - sum_of_numbers(n)
