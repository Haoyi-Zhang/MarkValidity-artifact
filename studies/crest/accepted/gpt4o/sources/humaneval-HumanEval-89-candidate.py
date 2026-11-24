def encrypt(s):
	return str.join('', (chr(((ord(char) - 97 + (2**2)) % 26) + 97) if char.islower() else char for char in s))
