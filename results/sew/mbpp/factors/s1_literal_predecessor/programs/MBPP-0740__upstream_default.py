def  tuple_to_dict(test_tup):
  res=dict(test_tup[idx : 2 + idx] for idx in range(0, len(test_tup), 2))
  return  (res) 
