
def is_Two_Alter(s):
	if len(set(s)) != 2:
		return False
	if any((s[i] != s[i % 2] for i in range(2, len(s)))):
		return False
	return True
