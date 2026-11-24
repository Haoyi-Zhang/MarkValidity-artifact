def  rotate_right(list, m):
  result =  list[-m:] + list[0:-m]
  return  result