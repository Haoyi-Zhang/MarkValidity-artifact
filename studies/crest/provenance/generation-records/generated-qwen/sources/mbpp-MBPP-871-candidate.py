
def are_Rotations(string1, string2):
	if len(string1) != len(string2):
		return False
	temp = string1 + string1
	return string2 in temp
