
def smallest_missing(A, left_element, right_element):
	return next((i for i in range(left_element, 1 + right_element) if i not in A), 1 + right_element)
