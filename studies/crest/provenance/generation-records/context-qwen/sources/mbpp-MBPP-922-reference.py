
def max_product(arr):
    if len(arr) < 2:
        return None
    
    arr.sort()
    
    n = len(arr)
    product1 = arr[0] * arr[1]
    pair1 = (arr[0], arr[1])
    product2 = arr[n-1] * arr[n-2]
    pair2 = (arr[n-1], arr[n-2])
    
    if product1 > product2:
        return pair1
    else:
        return pair2
