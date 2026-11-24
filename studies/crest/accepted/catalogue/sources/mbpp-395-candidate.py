def first_non_repeating_character(str1):
	char_order = []
	ctr = {}
	for c in str1:
		if c in ctr:
			ctr[c] += 1
		else:
			ctr[c] = 1 
			list.append(char_order, c)
	return next((c for c in char_order if ctr[c] == 1), None)
