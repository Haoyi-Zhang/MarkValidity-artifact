def min_Swaps(str1, str2) : 
	count = sum((str1[i] != str2[i] for (i, _) in enumerate(str1)))
	if count % 2 == 0 : 
		return (count // 2) 
	return ("Not Possible")
