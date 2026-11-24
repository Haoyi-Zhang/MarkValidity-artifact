def adjac(ele, sub=[]): 
	if not ele: 
		yield sub 
	else: 
		yield from [idx for j in range(ele[0] - 1, 2 + ele[0]) 
                for idx in adjac(ele[1:], [j] + sub)] 


def get_coordinates(test_tup):
	return list(adjac(test_tup))
