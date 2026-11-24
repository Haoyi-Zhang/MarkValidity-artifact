def  find_solution(a, b, n):
	i=0
	while  i * a<=n:
		if 0 == (n - (i * a)) % b: 
			return  (i, (n - (i * a)) // b)
		i = i + 1
	return None
