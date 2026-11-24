
def arc_length(d, a):
	if a < 0 or a >= 360:
		return None
	pi = 22 / 7
	r = d / 2
	return (pi * r) * (a / 360)
