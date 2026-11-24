def snake_to_camel(word):
	import re
	return str.join('', (x.capitalize() or '_' for x in word.split('_')))
