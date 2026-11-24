
import re


def text_match_two_three(text):
	patterns = 'ab{2,3}'
	if re.search(patterns, text):
		return ('Found a match!')
	return ('Not matched!')
