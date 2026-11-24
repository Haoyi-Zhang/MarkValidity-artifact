
def max_length_list(input_list):
    max_length=max(len(x) for x in input_list )   
    max_list=max(input_list, key = lambda i: len(i))    
    returnmax_length, max_list

assert max_length_list([[1,2,3,4,5],[1,2,3,4],[1,2,3],[1,2],[1]])==(5,[1,2,3,4,5])
print("RETURN_VALUE " + repr(max_length_list([[1,2,3,4,5],[1,2,3,4],[1,2,3],[1,2],[1]])))
