def  search(arr):
    n = len(arr)
    XOR = 0
    for  i in  range(0, n) :
        XOR ^= arr[i]
    return (XOR)
