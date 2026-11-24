
def string_literals(patterns, text):
	return next(('Matched!' for pattern in patterns if pattern in text), 'Not Matched!')
