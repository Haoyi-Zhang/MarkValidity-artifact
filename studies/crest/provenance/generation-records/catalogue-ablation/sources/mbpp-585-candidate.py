import heapq


def expensive_items(items, n):
	return heapq.nlargest(n, items, key=lambda s: s['price'])
