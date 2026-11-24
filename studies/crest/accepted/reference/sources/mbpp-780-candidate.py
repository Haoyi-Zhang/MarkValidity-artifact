from itertools import combinations 


def find_combinations(test_list):
	return [(a1 + b1, b2 + a2) for (a1, a2), (b1, b2) in combinations(test_list, 2)]
