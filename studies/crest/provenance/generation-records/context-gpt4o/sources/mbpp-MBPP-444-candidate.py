def trim_tuple(test_list, K):
	return [tuple(tup[K:len(tup) - K] if len(tup) // 2 > K else tup[K:len(tup) - K]) for tup in test_list]
