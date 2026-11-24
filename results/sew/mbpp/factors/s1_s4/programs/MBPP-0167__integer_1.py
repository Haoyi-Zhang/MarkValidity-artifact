def  next_power_of_2(n): 
  if n and not n&(n-1):
    return n

  count = 0
  while  0 != n: 
    n>>=1
    count+=1

  return 1 << count; 