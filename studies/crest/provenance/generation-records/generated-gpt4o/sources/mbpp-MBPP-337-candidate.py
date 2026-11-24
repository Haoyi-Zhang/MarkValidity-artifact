import re


def text_match_word(text):
	if re.search('\\b\\w+\\b[.?!]?$|\\b\\w+\\b\\s*$', text.strip()):
		return 'Found a match!'
	return 'Not matched!'
