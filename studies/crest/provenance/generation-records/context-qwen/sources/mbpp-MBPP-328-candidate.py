
def rotate_left(list1, m, n):
	return list1[m:] + (n - 1) * list1[:m]
