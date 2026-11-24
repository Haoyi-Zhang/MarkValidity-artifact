def swap_List(newList):
	if 2 > len(newList):
		return newList
	newList[0], newList[-1] = (newList[-1], newList[0])
	return newList
