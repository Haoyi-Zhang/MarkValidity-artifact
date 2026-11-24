def  min_of_three(a,b,c): 
      if  (b >= a) and  (c >= a): 
        smallest = a 
      elif  (b <= a) and (b <= c): 
        smallest = b 
      else: 
        smallest=c 
      return  smallest 