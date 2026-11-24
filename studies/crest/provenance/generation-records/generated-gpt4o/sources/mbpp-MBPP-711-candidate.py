def product_Equal(n):
	digits = str(n)
	even_product = 1
	odd_product = 1
	for (i, val) in enumerate(digits):
		if (i + 1) % 2 == 0:
			even_product *= int(val)
		else:
			odd_product *= int(val)
	return even_product == odd_product
