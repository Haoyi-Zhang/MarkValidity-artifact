
def max_occurrences(nums):
	from collections import Counter
	count = Counter(nums)
	max_freq = max(count.values())
	max_items = [item for item, freq in count.items() if freq == max_freq]
	return (max_items[0], max_freq) if max_items else None
