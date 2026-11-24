def remove(list1):
	return [str.join('', filter(lambda x: not x.isdigit(), word)) for word in list1]
