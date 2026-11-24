
import numpy as np


def find_zero(xs: list):
	roots = np.roots(xs)
	return round(roots.real[0], 2) if np.isclose(roots.imag, 0).all() else None
