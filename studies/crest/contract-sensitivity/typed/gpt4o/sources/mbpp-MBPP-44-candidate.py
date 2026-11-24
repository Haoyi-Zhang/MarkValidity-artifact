def text_match_string(text):
	import re
	if re.match('^\\w+', text):
		return 'Found a match!'
	return 'Not matched!'
