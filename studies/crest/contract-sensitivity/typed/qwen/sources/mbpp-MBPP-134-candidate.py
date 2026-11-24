
def check_last(arr, n, p):
	last_element = arr[-1]
	operation_result = (last_element + p) % 2
	if operation_result == 0:
		return "EVEN"
	return "ODD"
