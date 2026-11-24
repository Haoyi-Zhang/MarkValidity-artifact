def max_occurrences(nums):
	from collections import Counter
	count = Counter(nums)
	return max(count.items(), key=lambda x: x[1])
