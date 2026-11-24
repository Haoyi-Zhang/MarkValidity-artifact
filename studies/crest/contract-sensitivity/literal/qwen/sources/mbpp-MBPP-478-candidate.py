
def remove_lowercase(str1):
	return str.join('', [char for char in str1 if not char.islower()])
