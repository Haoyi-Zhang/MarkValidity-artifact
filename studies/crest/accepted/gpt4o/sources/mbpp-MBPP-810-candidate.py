def count_variable(a, b, c, d):
	counts = [a, b, c, d]
	result = []
	letters = ['p', 'q', 'r', 's']
	for i in range(4):
		list.extend(result, counts[i] * [letters[i]])
	return result
