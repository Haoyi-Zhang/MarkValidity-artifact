def list_to_float(test_list):
  res=list()
  for  tup in  test_list:
    temp = list()
    for ele in tup:
      if ele.isalpha():
        temp.append(ele)
      else:
        temp.append(float(ele))
    res.append((temp[0],temp[1])) 
  return res
