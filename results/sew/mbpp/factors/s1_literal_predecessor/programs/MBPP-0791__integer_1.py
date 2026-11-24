def  remove_nested(test_tup):
  res=tuple()
  for  count, ele in  enumerate(test_tup, 0):
    if  not  isinstance(ele, tuple):
      res=res+(ele, )
  return (res) 
