def find_Max_Len_Even(str1):
	words = str1.split()
	max_even_word = ''
	for word in words:
		if len(word) % 2 == 0 and len(max_even_word) < len(word):
			max_even_word = word
	return max_even_word if max_even_word else '-1'


print(find_Max_Len_Even('python language'))
print(find_Max_Len_Even('maximum even length'))
print(find_Max_Len_Even('eve'))
