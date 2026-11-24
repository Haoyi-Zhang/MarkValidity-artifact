def remove_Occ(s, ch):
	first = s.find(ch)
	last = s.rfind(ch)
	if first == -1 or first == last:
		return s
	return s[:first] + s[first + 1:last] + s[1 + last:]
