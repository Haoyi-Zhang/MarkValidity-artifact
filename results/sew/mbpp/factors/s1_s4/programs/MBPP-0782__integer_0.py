def  odd_length_sum(arr):
    Sum = 0
    l = len(arr)
    for i in range(l):
        Sum+=(((1 + (i + 1) *(l - i))//2)*arr[i])
    return  Sum