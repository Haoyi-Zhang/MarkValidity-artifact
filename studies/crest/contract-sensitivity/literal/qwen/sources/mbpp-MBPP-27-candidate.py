
def remove(lst):
	return [str.join('', filter(lambda c: not c.isdigit(), s)) for s in lst]
