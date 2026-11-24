
def reverse_vowels(str1):
	str_list = list(str1)
	j = len(str1) - 1
	vowels = "aeiouAEIOU"
	i = 0
    
	while i < j:
		if str_list[i] not in vowels:
			i += 1
		elif str_list[j] not in vowels:
			j -= 1
		else:
			str_list[i], str_list[j] = str_list[j], str_list[i]
			i += 1
			j -= 1
    
	return str.join('', str_list)
