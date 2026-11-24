
def generate_integers(a, b):
	if a > b:
		a, b = b, a
	return [i for i in range(a, 1 + b) if i % 2 == 0]
