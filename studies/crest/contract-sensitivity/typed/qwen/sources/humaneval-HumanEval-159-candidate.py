
def eat(number, need, remaining):
	if need <= remaining:
		return [need + number, remaining - need]
	return [remaining + number, 0]
