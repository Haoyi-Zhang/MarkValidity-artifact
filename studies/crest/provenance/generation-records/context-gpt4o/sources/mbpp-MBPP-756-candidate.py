import re


def text_match_zero_one(text):
	pattern = 'a(b?)'
	if re.search(pattern, text):
		return 'Found a match!'
	return 'Not matched!'
