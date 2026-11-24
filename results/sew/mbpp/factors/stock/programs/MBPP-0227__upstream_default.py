def  min_of_three(a,b,c): 
      if (b >= a) and (c >= a): 
        smallest=a 
      elif (a >= b) and  (c >= b): 
        smallest=b 
      else: 
        smallest = c 
      return  smallest 