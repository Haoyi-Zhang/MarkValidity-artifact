def adjac(ele, sub = []): 
  if ele: 
     yield from [idx for j in range(ele[0] - 1, ele[0] + 2) 
                for idx in adjac(ele[1:], sub + [j])] 
  else: 
     yield sub 
def get_coordinates(test_tup):
  return  list(adjac(test_tup))