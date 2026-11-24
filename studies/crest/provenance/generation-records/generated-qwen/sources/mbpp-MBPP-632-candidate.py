
def move_zero(num_list):
	non_zeroes = [num for num in num_list if num != 0]
	zeroes = []
	for _ in range((len(num_list) - len(non_zeroes))):
		list.append(zeroes, 0)
	return zeroes + non_zeroes
