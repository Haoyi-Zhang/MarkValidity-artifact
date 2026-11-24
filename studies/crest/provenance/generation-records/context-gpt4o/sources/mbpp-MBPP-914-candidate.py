def is_Two_Alter(s):
	if 2 > len(s):
		return False
	first_char = s[0]
	second_char = s[1]
	if first_char == second_char:
		return False
	if any(((i % 2 == 0 and val != first_char) or (i % 2 == 1 and val != second_char) for (i, val) in enumerate(s))):
		return False
	return True
