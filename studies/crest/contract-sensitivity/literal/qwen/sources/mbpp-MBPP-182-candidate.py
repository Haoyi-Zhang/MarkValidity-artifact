
import re


def find_character(string):
	uppercase_letters = re.findall(r'[A-Z]', string)
	lowercase_letters = re.findall(r'[a-z]', string)
	numeric_values = re.findall(r'\d', string)
	special_characters = re.findall(r'[^A-Za-z0-9\s]', string)
    
	return (uppercase_letters, lowercase_letters, numeric_values, special_characters)
