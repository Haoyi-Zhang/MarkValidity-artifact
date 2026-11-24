
def find_Average_Of_Cube(n):
	total_cube = sum(i**3 for i in range(1, 1 + n))
	return total_cube / n
