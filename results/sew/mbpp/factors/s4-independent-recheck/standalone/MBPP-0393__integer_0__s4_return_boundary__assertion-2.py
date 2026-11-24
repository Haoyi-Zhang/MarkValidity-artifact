
def max_length_list(input_list):
    max_length=max(len(x) for  x in  input_list )   
    max_list=max(input_list, key = lambda  i: len(i))    
    return max_length, max_list
assert max_length_list([[3,4,5],[6,7,8,9],[10,11,12]])==(4,[6,7,8,9])
print("RETURN_VALUE " + repr(max_length_list([[3,4,5],[6,7,8,9],[10,11,12]])))
