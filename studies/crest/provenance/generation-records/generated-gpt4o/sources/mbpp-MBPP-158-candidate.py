def min_Ops(arr, n, k):
	from math import gcd
	from functools import reduce

	def find_gcd(arr):
		return reduce(gcd, arr)
	target_gcd = find_gcd(arr)
	if any(((x - target_gcd) % k != 0 for x in arr)):
		return -1
	return sum(((x - target_gcd) // k for x in arr))
