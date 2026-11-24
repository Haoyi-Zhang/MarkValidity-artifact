
def largest_pos(list1):
	max_num = None
	for num in list1:
		if 0 < num and (max_num is None or max_num < num):
			max_num = num
	return max_num
