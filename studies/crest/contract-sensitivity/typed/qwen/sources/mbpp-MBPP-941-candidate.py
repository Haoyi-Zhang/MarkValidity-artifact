
def count_elim(num):
	return next((i for i, element in enumerate(num) if isinstance(element, tuple)), len(num))
