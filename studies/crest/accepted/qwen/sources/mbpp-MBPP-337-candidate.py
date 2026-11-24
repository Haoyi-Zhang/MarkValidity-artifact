
import re


def text_match_word(text):
	pattern = r'\b\w+\b[.!?]*$'
	if re.search(pattern, text):
		return 'Found a match!'
	return 'Not matched!'
