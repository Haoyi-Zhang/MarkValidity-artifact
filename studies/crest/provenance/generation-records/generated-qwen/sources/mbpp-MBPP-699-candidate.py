
def min_Swaps(str1, str2) :
	if len(str1) != len(str2):
		return "Not Possible"
    
	swaps = 0
	diff_positions = []
    
	list.extend(diff_positions, (i for (i, _) in enumerate(str1) if str1[i] != str2[i]))
    
	if len(diff_positions) % 2 != 0:
		return "Not Possible"
    
	for _ in range(0, len(diff_positions), 2):
		swaps += 1
    
	return swaps
