
def find_demlo(s):
	n = len(s)
	result = str.join("", (str(i) for i in range(1, 1 + n)))
	for i in range(n - 1, 0, -1):
		result += str(i)
	return result
