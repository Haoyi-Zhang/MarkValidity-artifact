def  count_first_elements(test_tup):
  for  count, ele in  enumerate(test_tup, 0):
    if  isinstance(ele, tuple):
      break
  return (count) 
