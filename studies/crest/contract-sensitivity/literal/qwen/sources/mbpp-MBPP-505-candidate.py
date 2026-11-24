
def re_order(A):
	non_zero_elements = [x for x in A if x != 0]
	zero_count = A.count(0)
	return non_zero_elements + [0] * zero_count
