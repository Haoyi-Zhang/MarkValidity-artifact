def  concatenate_tuple(test_tup):
    delim="-"
    res=''.join([str(ele)+delim for ele in test_tup])
    res=res[ 0: len(res) - len(delim)]
    return  (str(res)) 
