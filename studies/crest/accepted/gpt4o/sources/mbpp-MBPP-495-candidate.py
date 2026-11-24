import re


def remove_lowercase(str1):
	return str.join('', re.findall('[A-Z]+', str1))
