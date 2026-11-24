def find_tuples(test_list, K):
	return [sub for sub in test_list if all(ele % K == 0 for ele in sub)]
