
import re


def split_list(text):
	return re.findall(r'[A-Z][^A-Z]*', text)
