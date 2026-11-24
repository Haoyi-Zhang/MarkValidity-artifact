def  check_value(dict, n):
    result = all(n == x for x in dict.values()) 
    return  result