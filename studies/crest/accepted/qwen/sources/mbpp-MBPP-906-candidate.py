
import re


def extract_date(url):
	pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
	return re.findall(pattern, url)
