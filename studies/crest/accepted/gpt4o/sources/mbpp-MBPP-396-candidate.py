import re


def check_char(string):
	if re.match('^(.).*\\1$', string):
		return 'Valid'
	return 'Invalid'
