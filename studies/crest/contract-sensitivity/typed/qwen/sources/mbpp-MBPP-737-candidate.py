
import re


def check_str(string):
	if re.match(r'^[aeiouAEIOU]', string):
		return 'Valid'
	return 'Invalid'
