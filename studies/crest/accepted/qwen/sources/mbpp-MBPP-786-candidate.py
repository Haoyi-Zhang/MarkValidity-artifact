
def right_insertion(a, x):
	return next((i for (i, _) in enumerate(a) if x < a[i]), len(a))
