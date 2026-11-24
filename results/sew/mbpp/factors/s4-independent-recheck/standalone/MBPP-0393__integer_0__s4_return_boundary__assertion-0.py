
def max_length_list(input_list):
    max_length=max(len(x) for  x in  input_list )   
    max_list=max(input_list, key = lambda  i: len(i))    
    return max_length, max_list
assert max_length_list([[0], [1, 3], [5, 7], [9, 11], [13, 15, 17]])==(3, [13, 15, 17])
print("RETURN_VALUE " + repr(max_length_list([[0], [1, 3], [5, 7], [9, 11], [13, 15, 17]])))
