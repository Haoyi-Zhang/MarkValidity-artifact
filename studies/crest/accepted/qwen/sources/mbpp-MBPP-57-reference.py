
def find_Max_Num(arr,n) :
    arr.sort(reverse=True)
    max_num = int(''.join(map(str, arr)))
    return max_num
