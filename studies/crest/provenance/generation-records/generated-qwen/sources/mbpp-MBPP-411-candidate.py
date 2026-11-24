
import re


def snake_to_camel(word):
	return str.join('', (x.capitalize() or '_' for x in word.split('_')))
