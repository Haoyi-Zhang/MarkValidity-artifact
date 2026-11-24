
import re


def is_valid_URL(str1):
	regex = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'
	if (re.search(regex, str1)):
		return True
	return False
