
def remove_parenthesis(items):
	return [re.sub(r"\(.*?\)", "", item).strip() for item in items]
