
def count_Substring_With_Equal_Ends(s):
	n = len(s)
	return sum(((n - i) for i in range(n)))
