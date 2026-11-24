
import re


def text_match_wordz(text):
	pattern = r'\b\w*z\w*\b'
	if re.search(pattern, text):
		return ('Found a match!')
	return ('Not matched!')
