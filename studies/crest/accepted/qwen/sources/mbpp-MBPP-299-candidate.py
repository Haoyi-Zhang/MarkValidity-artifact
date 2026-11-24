
def max_aggregate(stdata):
	from collections import defaultdict

	aggregate = defaultdict(int)

	for name, score in stdata:
		aggregate[name] += score

	return max(aggregate.items(), key=lambda x: x[1])
