
import re


def extract_quotation(text1):
	pattern = r'\"([^\"]*)\"'
	return re.findall(pattern, text1)
