def catalan_number(num):
	if 1 >= num:
		return 1   
	res_num = 0
	for i in range(num):
		res_num += catalan_number(num - i - 1) * catalan_number(i)
	return res_num
