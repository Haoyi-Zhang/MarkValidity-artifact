def is_samepatterns(colors, patterns):    
	if len(colors) != len(patterns):
		return False    
	pset = set()
	sset = set()    
	sdict = {}
	for i in range(len(patterns)):
		set.add(pset, patterns[i])
		set.add(sset, colors[i])
		if patterns[i] not in dict.keys(sdict):
			sdict[patterns[i]] = []

		keys = sdict[patterns[i]]
		keys.append(colors[i])
		sdict[patterns[i]] = keys

	if len(pset) != len(sset):
		return False   

	if any((any((values[i] != values[i + 1] for i in range(len(values) - 1))) for values in dict.values(sdict))):
		return False

	return True
