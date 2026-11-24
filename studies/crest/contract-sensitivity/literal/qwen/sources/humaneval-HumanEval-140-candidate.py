
import re


def fix_spaces(text):
	text = text.replace(' ', '_')
	return re.sub(r'_{2,}', '-', text)
