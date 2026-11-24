
def find_First_Missing(array, start, end):
	return next((i for i in range(start, 1 + end) if i not in array), 1 + end)
