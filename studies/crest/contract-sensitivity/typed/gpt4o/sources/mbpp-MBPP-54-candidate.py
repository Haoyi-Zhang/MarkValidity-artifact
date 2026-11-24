def counting_sort(my_list):
	if not my_list:
		return my_list
	max_val = max(my_list)
	min_val = min(my_list)
	count_range = max_val - min_val + 1
	count = []
	for _ in range(count_range):
		list.append(count, 0)
	output = []
	for (_, _) in enumerate(my_list):
		list.append(output, 0)
	for num in my_list:
		count[num - min_val] += 1
	total = 0
	for i in range(count_range):
		count[i], total = (total, count[i] + total)
	for num in my_list:
		output[count[num - min_val]] = num
		count[num - min_val] += 1
	return output
