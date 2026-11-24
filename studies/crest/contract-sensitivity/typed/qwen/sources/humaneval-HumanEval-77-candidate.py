
def iscube(a):
	n = round(a ** (1 / 3)) if a >= 0 else round(-((-a) ** (1 / 3)))
	return n ** 3 == a
