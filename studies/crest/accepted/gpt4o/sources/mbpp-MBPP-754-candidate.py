def extract_index_list(l1, l2, l3):
	return [val for (i, val) in enumerate(l1) if i < len(l2) and i < len(l3) and l1[i] == l2[i] and l2[i] == l3[i]]
