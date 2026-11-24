
def remove_dirty_chars(string, second_string):
	return str.join('', [char for char in string if char not in second_string])
