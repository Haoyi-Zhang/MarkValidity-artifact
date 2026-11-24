def magic_square_test(my_matrix):
	iSize = len(my_matrix[0])
	sum_list = []
	list.extend(sum_list, [sum (lines) for lines in my_matrix])   
	list.extend(sum_list, (sum(row[col] for row in my_matrix) for col in range(iSize)))
	result1 = 0
	for i in range(0, iSize):
		result1 += my_matrix[i][i]
	list.append(sum_list, result1)      
	result2 = 0
	for i in range(iSize - 1, -1, -1):
		result2 += my_matrix[i][i]
	list.append(sum_list, result2)
	if 1 < len(set(sum_list)):
		return False
	return True
