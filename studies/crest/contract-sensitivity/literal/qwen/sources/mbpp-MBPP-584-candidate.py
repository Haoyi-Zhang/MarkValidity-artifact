
import re


def find_adverbs(text):
	adverb_pattern = r"\b\w+ly\b"
	matches = re.finditer(adverb_pattern, text)
	result = ""
	for match in matches:
		start, end = match.span()
		adverb = match.group(0)
		if result:
			result += "; "
		result += f"{start}-{end}: {adverb}"
	return result
