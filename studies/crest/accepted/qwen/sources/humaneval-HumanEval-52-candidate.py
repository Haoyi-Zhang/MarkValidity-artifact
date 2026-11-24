
def below_threshold(l: list, t: int):
	return all(t > x for x in l)
