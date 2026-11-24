
def unique_product(list_data):
    unique_numbers = set(list_data)
    product = 1
    for number in unique_numbers:
        product *= number
    return product
