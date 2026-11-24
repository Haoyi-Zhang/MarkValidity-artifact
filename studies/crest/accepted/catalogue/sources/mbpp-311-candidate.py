def set_left_most_unset_bit(n): 
	if not (n & (n + 1)): 
		return n 
	temp = n 
	count = 0 
	pos = 0 
	while temp: 
		if not (temp & 1): 
			pos = count      
		count += 1; temp >>= 1
	return (n | (1 << (pos)))
