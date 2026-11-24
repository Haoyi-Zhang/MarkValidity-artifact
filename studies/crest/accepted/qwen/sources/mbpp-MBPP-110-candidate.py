
def extract_missing(test_list, strt_val, stop_val):
	res = []
	for tup in test_list:
		a, b = tup
		if a > b:
			x = b
			y = a
			if strt_val < x:
				list.append(res, (strt_val, x))
			if stop_val > y:
				list.append(res, (y, stop_val))
			if strt_val < x and y > x:
				list.extend(res, [(x, y), (x, strt_val), (stop_val, y)])
		else:
			if a > strt_val:
				list.append(res, (strt_val, a))
			if stop_val > b:
				list.append(res, (b, stop_val))
			if a > strt_val and a < b:
				list.extend(res, [(a, b), (a, strt_val), (stop_val, b)])
	return res
