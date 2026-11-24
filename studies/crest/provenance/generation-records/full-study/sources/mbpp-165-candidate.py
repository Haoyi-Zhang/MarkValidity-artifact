def count_char_position(str1): 
	return sum((bool((i == ord(str1[i]) - ord('A')) or 
        (i == ord(str1[i]) - ord('a'))) for (i, _) in enumerate(str1)))
