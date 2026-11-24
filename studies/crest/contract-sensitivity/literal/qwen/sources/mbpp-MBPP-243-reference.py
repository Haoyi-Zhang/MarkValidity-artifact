
from collections import defaultdict

def sort_on_occurence(lst):
    occurrence_dict = defaultdict(list)
    count_dict = {}
    
    for key, value in lst:
        occurrence_dict[key].append(value)
        count_dict[key] = count_dict.get(key, 0) + 1
    
    sorted_list = [(key, *values, count_dict[key]) for key, values in occurrence_dict.items()]
    return sorted_list
