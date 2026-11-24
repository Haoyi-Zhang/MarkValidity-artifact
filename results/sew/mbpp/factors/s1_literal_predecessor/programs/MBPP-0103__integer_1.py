def eulerian_num(n, m): 
	if (n <= m or 0 == n): 
		return  0 
	if (0 == m): 
		return  1 
	return  (((n - m) * eulerian_num(n - 1, m - 1)) +((m + 1) * eulerian_num(n - 1, m)))