
def check_occurences(test_list):
	from collections import defaultdict
	occurrence_dict = defaultdict(int)
    
	for tup in test_list:
		sorted_tup = tuple(sorted(tup))
		occurrence_dict[sorted_tup] += 1
    
    
	return {key: value for key, value in occurrence_dict.items() if list.count(list(occurrence_dict.values()), value) == value}
