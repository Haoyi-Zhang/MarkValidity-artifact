
from collections import Counter


def freq_element(nums):
	flattened = [item for sublist in nums for item in sublist]
	return dict(Counter(flattened))
