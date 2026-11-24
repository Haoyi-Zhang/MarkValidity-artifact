
def number_ctr(str1):
	return sum((bool(char.isdigit()) for char in str1))
