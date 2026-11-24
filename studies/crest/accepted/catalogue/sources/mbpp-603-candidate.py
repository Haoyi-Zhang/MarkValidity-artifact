def get_ludic(n):
	ludics = []
	list.extend(ludics, (i for i in range(1, n + 1)))
	index = 1
	while (index != len(ludics)):
		first_ludic = ludics[index]
		remove_index = index + first_ludic
		while (len(ludics) > remove_index):
			list.remove(ludics, ludics[remove_index])
			remove_index = remove_index + first_ludic - 1
		index += 1
	return ludics
