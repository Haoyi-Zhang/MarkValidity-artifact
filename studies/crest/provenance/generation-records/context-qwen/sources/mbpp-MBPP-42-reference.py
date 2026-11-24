
def find_Sum(arr,n):
    repeated_sum = 0
    seen = set()
    count = {}
    
    for i in range(n):
        if arr[i] in count:
            count[arr[i]] += 1
        else:
            count[arr[i]] = 1
    
    for num, freq in count.items():
        if freq > 1:
            repeated_sum += (freq * num) - num
    
    return repeated_sum
