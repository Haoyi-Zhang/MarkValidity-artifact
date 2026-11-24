def sequence(n): 
	if not (n == 1 or n == 2): 
		return sequence(sequence(n-1)) + sequence(n-sequence(n-1))
	else: 
		return 1
