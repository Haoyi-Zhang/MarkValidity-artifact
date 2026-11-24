def get_ludic(n):
	ludics = []
	list.extend(ludics, (i for i in range(1, 1 + n)))
	index = 1
	while (index != len(ludics)):
		first_ludic = ludics[index]
		remove_index = first_ludic + index
		while (len(ludics) > remove_index):
			list.remove(ludics, ludics[remove_index])
			remove_index = first_ludic + remove_index - 1
		index += 1
	return ludics
