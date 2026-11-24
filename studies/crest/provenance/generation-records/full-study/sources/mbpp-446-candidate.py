from collections import Counter 


def count_Occurrence(tup, lst): 
	return sum((item in lst for item in tup))
