def rotate_left(list1, m, n):
	return (list1[m:] + list1[:m])[:len(list1) - n] if len(list1) - m >= n else list1[m:] + list1[:m]
