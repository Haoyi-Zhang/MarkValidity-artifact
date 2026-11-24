
from collections import defaultdict


def sort_on_occurence(lst):
	occurrence_dict = defaultdict(list)
	count_dict = {}
    
	for key, value in lst:
		occurrence_dict[key].append(value)
		count_dict[key] = dict.get(count_dict, key, 0) + 1
    
	return [(key, *values, count_dict[key]) for key, values in occurrence_dict.items()]
