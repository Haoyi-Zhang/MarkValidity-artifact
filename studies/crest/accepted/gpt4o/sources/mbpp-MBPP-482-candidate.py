import re


def match(text):
	if re.search('[A-Z][a-z]+', text):
		return 'Yes'
	return 'No'
