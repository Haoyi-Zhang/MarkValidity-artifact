def catalan_number(num):
	if 1 >= num:
		return 1
	catalan = []
	for _ in range((1 + num)):
		list.append(catalan, 0)
	catalan[0], catalan[1] = (1, 1)
	for i in range(2, 1 + num):
		for j in range(i):
			catalan[i] += catalan[i - j - 1] * catalan[j]
	return catalan[num]
