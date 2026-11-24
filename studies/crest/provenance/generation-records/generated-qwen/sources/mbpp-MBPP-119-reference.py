
    low = 0
    high = n - 1
    
    while low < high:
        mid = low + (high - low) // 2
        
        # Check if the mid is even or odd
        if mid % 2 == 0:
            # If mid element is equal to next element
            if arr[mid] == arr[mid + 1]:
                low = mid + 2
            else:
                high = mid
        else:
            # If mid element is equal to previous element
            if arr[mid] == arr[mid - 1]:
                low = mid + 1
            else:
                high = mid
    
    return arr[low]
