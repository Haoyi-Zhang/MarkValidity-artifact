def min_flip_to_make_string_alternate(str1):
	n = len(str1)
	s1 = ''
	s2 = ''
	for i in range(n):
		s1 += '0' if i % 2 == 0 else '1'
		s2 += '1' if i % 2 == 0 else '0'
	flips1 = 0
	flips2 = 0
	for i in range(n):
		if str1[i] != s1[i]:
			flips1 += 1
		if str1[i] != s2[i]:
			flips2 += 1
	return min(flips1, flips2)
