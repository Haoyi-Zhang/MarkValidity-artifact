def Diff(li1, li2):
	return list(set.symmetric_difference(set(li1), set(li2)))
