
def digit_distance_nums(n1, n2):
	str_n1 = str(n1)
	str_n2 = str(n2)
	max_len = max(len(str_n1), len(str_n2))
	str_n1 = str_n1.zfill(max_len)
	str_n2 = str_n2.zfill(max_len)
    
    
	return sum((abs(int(d1) - int(d2)) for d1, d2 in zip(str_n1, str_n2)))
