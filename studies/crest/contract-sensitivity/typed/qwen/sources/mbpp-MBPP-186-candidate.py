
import re


def check_literals(text, patterns):
	return next(('Matched!' for pattern in patterns if re.search(pattern, text)), 'Not Matched!')
