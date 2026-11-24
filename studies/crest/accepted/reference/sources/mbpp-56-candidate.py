def rev(num):    
	rev_num = 0
	while (0 < num):  
		rev_num = (10 * rev_num + num % 10) 
		num = num // 10  
	return rev_num  


def check(n):    
	return (2 * rev(n) == 1 + n)
