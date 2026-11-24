import re


def text_match_one(text):
	pattern = 'ab+'
	if re.search(pattern, text):
		return 'Found a match!'
	return 'Not matched!'
