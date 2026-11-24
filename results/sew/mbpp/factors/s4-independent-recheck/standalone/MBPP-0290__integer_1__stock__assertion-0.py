
def max_length(list1):
    max_length = max(len(x) for x in list1 )  
    max_list = max((x) for x in   list1)
    returnmax_length, max_list

assert max_length([[0], [1, 3], [5, 7], [9, 11], [13, 15, 17]])==(3, [13, 15, 17])
print("RETURN_VALUE " + repr(max_length([[0], [1, 3], [5, 7], [9, 11], [13, 15, 17]])))
