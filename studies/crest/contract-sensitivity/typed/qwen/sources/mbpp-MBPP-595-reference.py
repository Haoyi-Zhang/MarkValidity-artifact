
def min_Swaps(str1, str2):
    if len(str1) != len(str2):
        return "Not Possible"
    
    count_0 = 0
    count_1 = 0
    for i in range(len(str1)):
        if str1[i] != str2[i]:
            if str1[i] == '0':
                count_0 += 1
            else:
                count_1 += 1
    
    if count_0 % 2 != 0 or count_1 % 2 != 0:
        return "Not Possible"
    
    return (count_0 // 2) + (count_1 // 2)
