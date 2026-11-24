def remove_replica(test_tup):
	from collections import Counter
	count = Counter(test_tup)
	return tuple(('MSP' if count[item] > 1 and i > test_tup.index(item) else item for i, item in enumerate(test_tup)))
