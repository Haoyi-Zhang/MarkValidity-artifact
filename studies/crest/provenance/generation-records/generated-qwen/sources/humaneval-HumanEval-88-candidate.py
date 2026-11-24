
def sort_array(array):
	if not array:
		return []
    
	if len(array) == 1:
		return array[:]
    
	sum_first_last = array[0] + array[-1]
    
	if sum_first_last % 2 == 0:
		return sorted(array, reverse=True)
	return sorted(array)
