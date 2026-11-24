
def min_val(listval):
	numeric_values = [x for x in listval if isinstance(x, (int, float))]
	return min(numeric_values)
