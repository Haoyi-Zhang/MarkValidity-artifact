
def find_Max_Len_Even(str1):
	words = str1.split()
	max_len_even_word = ""
    
	for word in words:
		if len(word) % 2 == 0 and len(max_len_even_word) < len(word):
			max_len_even_word = word
    
	return max_len_even_word if max_len_even_word else "-1"
