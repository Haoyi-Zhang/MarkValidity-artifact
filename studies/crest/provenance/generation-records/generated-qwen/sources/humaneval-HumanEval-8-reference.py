
    total_sum = 0
    total_product = 1
    
    for number in numbers:
        total_sum += number
        total_product *= number
    
    return total_sum, total_product
