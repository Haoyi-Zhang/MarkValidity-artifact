
def count_Pairs(arr, n):
	from collections import Counter
	freq = Counter(arr)
	return sum(((val - 1) * val // 2 for val in freq.values() if val > 1))
