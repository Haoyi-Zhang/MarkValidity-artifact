
def count_Char(str1, x):
	n = len(str1)
	full_repeats = str1.count(x) * (n // 3)
	remaining_part = str1[:n % 3]
	return full_repeats + remaining_part.count(x)
