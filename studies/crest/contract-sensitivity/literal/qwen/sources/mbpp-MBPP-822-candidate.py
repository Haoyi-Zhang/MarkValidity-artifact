
import re


def pass_validity(p):
	if 8 > len(p):
		return False
	if p.islower() or p.isupper():
		return False
	if not re.search("[0-9]", p):
		return False
	if not re.search("[!@#$%^&*(),.?\":{}|<>]", p):
		return False
	return True
