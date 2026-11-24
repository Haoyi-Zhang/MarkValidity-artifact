def get_Char(strr):  
	summ = sum(((ord(val) - ord('a') + 1) for (_, val) in enumerate(strr)))
	if (summ % 26 == 0): 
		return ord('z') 
	summ = summ % 26
	return chr(summ + ord('a') - 1)
