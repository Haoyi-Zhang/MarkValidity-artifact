def increment_numerics(test_list, K):
	return [str(K + int(item)) if item.isdigit() else item for item in test_list]
