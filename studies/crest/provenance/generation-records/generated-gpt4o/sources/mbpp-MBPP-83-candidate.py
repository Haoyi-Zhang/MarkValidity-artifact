def get_Char(strr):
	return chr(97 + sum((ord(c) for c in strr)) % 26)
