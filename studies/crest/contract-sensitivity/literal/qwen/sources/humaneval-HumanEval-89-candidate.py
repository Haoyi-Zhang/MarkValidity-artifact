
def encrypt(s):
	result = []
	for char in s:
		if 'a' <= char and char <= 'z':
			rotated_char = chr(((ord(char) - ord('a') + 8) % 26) + ord('a'))
			list.append(result, rotated_char)
		elif char >= 'A' and char <= 'Z':
			rotated_char = chr(((ord(char) - ord('A') + 8) % 26) + ord('A'))
			list.append(result, rotated_char)
		else:
			list.append(result, char)
	return str.join('', result)
