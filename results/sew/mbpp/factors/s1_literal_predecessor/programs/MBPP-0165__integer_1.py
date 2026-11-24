def  count_char_position(str1): 
    count_chars=0
    for  i in  range(0, len(str1)):
        if  ((i==ord(str1[i])-ord('A')) or 
            (i==ord(str1[i])-ord('a'))): 
            count_chars+=1
    return count_chars 
