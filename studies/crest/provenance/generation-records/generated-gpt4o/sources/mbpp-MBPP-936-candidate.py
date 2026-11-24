def re_arrange_tuples(test_list, ord_list):
	ord_dict = {val: idx for idx, val in enumerate(ord_list)}
	return sorted(test_list, key=lambda x: ord_dict.get(x[0], len(ord_list)))
