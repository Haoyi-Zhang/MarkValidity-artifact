
import re


def end_num(string):
	return bool(re.search(r'\d$', string))
