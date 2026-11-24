def overlapping(list1, list2):  
	if any((any(((list1[i] == list2[j]) for j in range(len(list2)))) for i in range(len(list1)))):
		return True
	return False
