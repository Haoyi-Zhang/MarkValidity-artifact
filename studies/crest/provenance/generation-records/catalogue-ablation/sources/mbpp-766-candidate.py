def pair_wise(l1):
	temp = []
	for i in range(len(l1) - 1):
		current_element = l1[i]
		next_element = l1[i + 1]
		x = (current_element, next_element)
		list.append(temp, x)
	return temp
