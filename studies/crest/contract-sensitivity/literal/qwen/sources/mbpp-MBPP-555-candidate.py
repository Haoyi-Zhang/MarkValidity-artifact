
def difference(n):
	def sum_of_squares(x):
		return sum(i**3 for i in range(1, 1 + x))
    
	def sum_of_numbers(x):
		return sum(i for i in range(1, 1 + x))
    
	return sum_of_squares(n) - sum_of_numbers(n)
