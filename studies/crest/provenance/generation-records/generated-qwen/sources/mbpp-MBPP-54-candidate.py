
def counting_sort(my_list):
	if not my_list:
		return []

	max_value = max(my_list)
	count = []
	for _ in range((max_value + 1)):
		list.append(count, 0)

	for num in my_list:
		count[num] += 1

	sorted_index = 0
	for i, freq in enumerate(count):
		for _ in range(freq):
			my_list[sorted_index] = i
			sorted_index += 1

	return my_list
