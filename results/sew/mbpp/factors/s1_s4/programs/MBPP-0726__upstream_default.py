def  multiply_elements(test_tup):
  res=tuple(j * i for i, j in zip(test_tup, test_tup[1:]))
  return  (res) 
