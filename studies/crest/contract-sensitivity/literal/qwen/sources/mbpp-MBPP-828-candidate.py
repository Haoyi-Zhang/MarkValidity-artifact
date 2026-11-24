
def count_alpha_dig_spl(string):
	alpha_count = sum(c.isalpha() for c in string)
	dig_count = sum(c.isdigit() for c in string)
	spl_count = sum(not c.isalnum() and not c.isspace() for c in string)
	return (alpha_count, dig_count, spl_count)
