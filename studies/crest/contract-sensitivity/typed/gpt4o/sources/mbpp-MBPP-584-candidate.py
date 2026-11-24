import re


def find_adverbs(text):
	matches = []
	for match in re.finditer('\\b\\w+ly\\b', text):
		start, end = match.span()
		list.append(matches, f'{start}-{end}: {match.group()}')
	return str.join(', ', matches) if matches else None
