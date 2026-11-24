
def check(arr, n):
    left = 0
    right = n - 1
    
    while left < right and arr[left] <= arr[left + 1]:
        left += 1
    
    if left == n - 1:
        return True
    
    while right > left and arr[right] >= arr[right - 1]:
        right -= 1
    
    if arr[left] <= arr[right]:
        return True
    
    return False
