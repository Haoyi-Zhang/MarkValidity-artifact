from collections import defaultdict


def max_occurrences(nums):
	dict1 = defaultdict(int)
	for i in nums:
		dict1[i] += 1
	result = max(dict1.items(), key=lambda x: x[1]) 
	return result[0]
