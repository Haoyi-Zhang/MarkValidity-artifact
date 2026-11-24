
def get_ludic(n):
	ludics = list(iter(range(1, 1 + n)))
	index = 1
	while len(ludics) > index:
		first_ludic = ludics[index]
		ludics = [x for i, x in enumerate(ludics) if (i + 1) % first_ludic != 0 or (i + 1) == first_ludic]
		index += 1
	return ludics
