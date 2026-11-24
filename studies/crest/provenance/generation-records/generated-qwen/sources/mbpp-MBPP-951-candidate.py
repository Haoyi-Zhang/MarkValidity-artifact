
def max_similar_indices(test_list1, test_list2):
	return [max(pair1, pair2) for pair1, pair2 in zip(test_list1, test_list2)]
