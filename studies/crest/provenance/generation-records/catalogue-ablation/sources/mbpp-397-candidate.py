def median_numbers(a, b, c):
	return (a if a < c else (b if b > c else c)) if a > b else (a if a > c else (b if b < c else c))
