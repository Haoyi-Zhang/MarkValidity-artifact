
import re


def text_match_string(text):
	pattern = '^\w+'
	if re.match(pattern, text):
		return ('Found a match!')
	return ('Not matched!')
