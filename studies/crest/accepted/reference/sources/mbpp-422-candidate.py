def find_Average_Of_Cube(n):  
	sum = sum((i * i**2 for i in range(1, 1 + n)))
	return round(sum / n, 6)
