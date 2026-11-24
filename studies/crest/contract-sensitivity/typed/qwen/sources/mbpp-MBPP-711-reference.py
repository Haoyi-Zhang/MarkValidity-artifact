
def product_Equal(n):
    str_n = str(n)
    even_product = 1
    odd_product = 1
    
    for i in range(len(str_n)):
        if i % 2 == 0:
            even_product *= int(str_n[i])
        else:
            odd_product *= int(str_n[i])
    
    return even_product == odd_product
