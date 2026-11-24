def swap_List(newList):
	if 2 <= len(newList):
		newList[0], newList[-1] = (newList[-1], newList[0])
	return newList
