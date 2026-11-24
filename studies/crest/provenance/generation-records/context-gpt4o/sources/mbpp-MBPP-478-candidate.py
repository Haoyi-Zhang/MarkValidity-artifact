def remove_lowercase(str1):
	return str.join('', [ch for ch in str1 if not ch.islower()])
