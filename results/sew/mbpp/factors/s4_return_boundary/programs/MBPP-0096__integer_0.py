def  divisor(n):
  for i in range(n):
    x=len([i for  i in  range(1,1+n) if  not  n%i])
  return  x