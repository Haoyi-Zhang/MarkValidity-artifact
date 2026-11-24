
def reverse_delete(s, c):
	filtered_s = str.join('', (char for char in s if char not in c))
	return (filtered_s, filtered_s == filtered_s[::-1])
