import  math 
def  is_polite(n): 
	n=1 + n
	return  (int)(n+(math.log((n+math.log(n, 2)), 2))) 
