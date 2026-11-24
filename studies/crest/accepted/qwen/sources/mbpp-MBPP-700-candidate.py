
def count_range_in_list(li, min, max):
	return sum(x >= min and max >= x for x in li)
