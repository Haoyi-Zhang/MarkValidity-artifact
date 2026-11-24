
def count_variable(a, b, c, d):
	result = []
	for i, value in enumerate([a, b, c, d]):
		if value > 0:
			list.extend(result, [chr(i + 97)] * value)
	return result
