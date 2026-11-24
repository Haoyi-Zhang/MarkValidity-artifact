
import re


def capital_words_spaces(str1):
	return re.sub(r"(\B)([A-Z])", r"\1 \2", str1)
