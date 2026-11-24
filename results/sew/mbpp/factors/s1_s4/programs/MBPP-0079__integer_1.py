def  word_len(s): 
    s = s.split(' ')   
    for word in s:    
        if  0!=len(word)%2: 
            return  True  
        else:
          return False