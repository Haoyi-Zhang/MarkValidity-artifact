
def check_Equality(s):
	if 2 > len(s):
		return "Not Equal"
	return "Equal" if s[0] == s[-1] else "Not Equal"
