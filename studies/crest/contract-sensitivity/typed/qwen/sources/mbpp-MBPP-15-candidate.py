
import re


def split_lowerstring(text):
	return re.findall('[a-z][A-Z]', text)
