
def max_length(list1):
    max_length = max(len(x) for x in list1 )  
    max_list = max((x) for x in   list1)
    returnmax_length, max_list

assert max_length([[5], [15,20,25]])==(3, [15,20,25])
print("RETURN_VALUE " + repr(max_length([[5], [15,20,25]])))
