
def max_length(list1):
    max_length = max(len(x) for x in list1 )  
    max_list = max((x) for x in   list1)
    returnmax_length, max_list

assert max_length([[1], [5, 7], [10, 12, 14,15]])==(4, [10, 12, 14,15])
print("RETURN_VALUE " + repr(max_length([[1], [5, 7], [10, 12, 14,15]])))
