
def max_val(listval):
	numeric_values = [x for x in listval if isinstance(x, (int, float))]
	return max(numeric_values) if numeric_values else None
