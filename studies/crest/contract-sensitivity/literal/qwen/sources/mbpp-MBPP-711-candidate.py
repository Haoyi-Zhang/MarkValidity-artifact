
def product_Equal(n):
	str_n = str(n)
	even_product = 1
	odd_product = 1
    
	for (i, val) in enumerate(str_n):
		if i % 2 == 0:
			even_product *= int(val)
		else:
			odd_product *= int(val)
    
	return even_product == odd_product
