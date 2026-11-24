
import re


def is_decimal(num):
	pattern = r'^\d+\.\d{2}$'
	return bool(re.match(pattern, num))
