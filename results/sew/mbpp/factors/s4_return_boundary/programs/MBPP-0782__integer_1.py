def  odd_length_sum(arr):
    Sum = 0
    l = len(arr)
    for  i in  range(0, l):
        Sum += ((((i + 1) *(l - i) + 1) // 2) * arr[i])
    return Sum
