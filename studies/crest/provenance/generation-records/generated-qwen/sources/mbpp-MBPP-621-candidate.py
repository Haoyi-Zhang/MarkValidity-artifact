
def increment_numerics(test_list, K):
	return [str(K + int(x)) if x.isdigit() else x for x in test_list]
