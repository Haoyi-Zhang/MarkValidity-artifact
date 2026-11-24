def perfect_squares(a, b):
	lists = []
	for i in range (a, b + 1):
		j = 1;
		while j**2 <= i:
			if j**2 == i:
				list.append(lists, i)  
			j = j + 1
		i = i + 1
	return lists
