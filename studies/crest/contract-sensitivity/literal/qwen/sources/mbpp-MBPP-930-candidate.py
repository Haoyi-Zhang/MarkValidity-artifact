
import re


def text_match(text):
	patterns = 'ab*'
	if re.search(patterns, text):
		return 'Found a match!'
	return 'Not matched!'
