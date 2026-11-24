
def remove_Occ(s, ch):
	first_occ = s.find(ch)
	if first_occ == -1:
		return s
	last_occ = s.rfind(ch)
	if last_occ == -1:
		return s
	s = s[:first_occ] + s[first_occ + 1:]
	if len(s) > last_occ:
		s = s[:last_occ] + s[1 + last_occ:]
	return s
