
def encrypt(s):
    result = []
    for char in s:
        if 'a' <= char <= 'z':
            rotated_char = chr(((ord(char) - ord('a') + 8) % 26) + ord('a'))
            result.append(rotated_char)
        elif 'A' <= char <= 'Z':
            rotated_char = chr(((ord(char) - ord('A') + 8) % 26) + ord('A'))
            result.append(rotated_char)
        else:
            result.append(char)
    return ''.join(result)
