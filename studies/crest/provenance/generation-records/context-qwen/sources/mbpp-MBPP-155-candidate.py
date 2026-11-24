
def even_bit_toggle_number(n):
	result = 0
	mask = 0
	pos = 0
    
	while (1 << pos) <= n:
		if pos % 2 == 1:
			mask |= (1 << pos)
		pos += 1
    
	return n ^ mask
