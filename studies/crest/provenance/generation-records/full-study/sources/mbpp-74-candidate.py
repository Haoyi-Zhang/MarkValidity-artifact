def is_samepatterns(colors, patterns):    
	if len(colors) != len(patterns):
		return False    
	pset = set()
	sset = set()    
	sdict = {}
	for (i, val) in enumerate(patterns):
		set.add(pset, val)
		set.add(sset, colors[i])
		if val not in dict.keys(sdict):
			sdict[val] = []

		keys = sdict[val]
		keys.append(colors[i])
		sdict[val] = keys

	if len(pset) != len(sset):
		return False   

	if any((any((values[i] != values[i + 1] for i in range(len(values) - 1))) for values in dict.values(sdict))):
		return False

	return True
