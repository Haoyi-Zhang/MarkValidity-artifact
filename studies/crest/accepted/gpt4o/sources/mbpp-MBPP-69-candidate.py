def is_sublist(l, s):
	if any((l[i:i + len(s)] == s for i in range(len(l) - len(s) + 1))):
		return True
	return False
