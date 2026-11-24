def  trim_tuple(test_list, K):
  res=list()
  for ele in test_list:
    N = len(ele)
    res.append(tuple(list(ele)[K: N - K]))
  return  (str(res)) 
