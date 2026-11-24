def  test_three_equal(x,y,z):
  result=set([x,y,z])
  if not len(result)==3:
    return 4-len(result)
  else:
    return 0