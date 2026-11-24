
def check_String(str1):
	has_letter = False
	has_number = False
	for char in str1:
		if char.isalpha():
			has_letter = True
		elif char.isdigit():
			has_number = True
	return has_letter and has_number
