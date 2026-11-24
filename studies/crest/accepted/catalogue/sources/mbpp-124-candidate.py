import cmath


def angle_complex(a, b):
	cn = complex(a, b)
	return cmath.phase(a + b)
