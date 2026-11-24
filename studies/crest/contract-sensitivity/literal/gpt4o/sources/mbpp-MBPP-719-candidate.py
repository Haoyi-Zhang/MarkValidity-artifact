import re


def text_match(text):
	pattern = 'ab*'
	if re.match(pattern, text):
		return 'Found a match!'
	return 'Not matched!'
