
def convert_list_dictionary(l1, l2, l3):
	return [{val: {l2[i]: l3[i]}} for (i, val) in enumerate(l1)]
