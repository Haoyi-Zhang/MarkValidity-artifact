def remove_words(list1, charlist):
	result = []
	for item in list1:
		for char in charlist:
			item = item.replace(char, '')
		list.append(result, item.strip())
	return result
