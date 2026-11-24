def remove_odd(str1):
	return str.join('', [val for (i, val) in enumerate(str1) if i % 2 != 0])
