
def check_if_last_char_is_a_letter(txt):
	txt = txt.strip()
	if not txt:
		return False
	last_word = txt.split(' ')[-1]
	return len(last_word) == 1 and last_word.isalpha()
