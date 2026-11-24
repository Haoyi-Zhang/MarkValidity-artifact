def all_Characters_Same(s) :
	n = len(s)
	if any((s[i] != s[0] for i in range(1, n))):
		return False
	return True
