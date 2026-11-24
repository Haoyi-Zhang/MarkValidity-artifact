
from collections import defaultdict

def count_element_freq(test_tuple):
    freq_dict = defaultdict(int)
    
    def flatten(tup):
        for item in tup:
            if isinstance(item, tuple):
                yield from flatten(item)
            else:
                yield item
    
    for element in flatten(test_tuple):
        freq_dict[element] += 1
    
    return dict(freq_dict)
