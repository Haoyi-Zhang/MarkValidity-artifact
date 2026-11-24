
def closest_integer(value):
	float_value = float(value)
	if 0 < float_value:
		return int(0.5 + float_value)
	return int(float_value - 0.5)
