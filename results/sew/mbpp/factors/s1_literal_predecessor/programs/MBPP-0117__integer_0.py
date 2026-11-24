def list_to_float(test_list):
  res = []
  for tup in test_list:
    temp = []
    for ele in tup:
      if not ele.isalpha():
        temp.append(float(ele))
      else:
        temp.append(ele)
    res.append((temp[0],temp[1])) 
  return res