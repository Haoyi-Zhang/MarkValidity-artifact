def check_literals(text, patterns):
	import re
	return next(('Matched!' for pattern in patterns if re.search(pattern, text)), 'Not Matched!')
