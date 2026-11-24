
def mul_even_odd(list1):
	even_found = False
	odd_found = False
	product = 1
    
	for num in list1:
		if not even_found and num % 2 == 0:
			product *= num
			even_found = True
		elif not odd_found and num % 2 != 0:
			product *= num
			odd_found = True
        
		if even_found and odd_found:
			break
    
	return product
