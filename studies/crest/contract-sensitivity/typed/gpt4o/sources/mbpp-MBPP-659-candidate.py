def Repeat(x):
	return list({item for item in x if 1 < x.count(item)})
