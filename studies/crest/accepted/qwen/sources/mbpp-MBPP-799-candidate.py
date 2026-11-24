
def left_Rotate(n, d):
	# Assuming a 32-bit integer for rotation
	return (n << d) | (n >> (32 - d))
