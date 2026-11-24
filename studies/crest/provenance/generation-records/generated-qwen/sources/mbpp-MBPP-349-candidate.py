
def check(string) :
	if all(char in '01' for char in string):
		return "Yes"
	return "No"
