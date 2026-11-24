from operator import itemgetter 


def index_minimum(test_list):
	return min(test_list, key=itemgetter(1))[0]
