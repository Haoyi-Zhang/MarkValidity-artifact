
    import heapq
    
    # Generate all possible products
    products = []
    for num1 in nums1:
        for num2 in nums2:
            products.append(num1 * num2)
    
    # Find the N largest products
    largest_products = heapq.nlargest(N, products)
    
    return largest_products
