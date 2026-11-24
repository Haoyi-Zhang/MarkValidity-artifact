import math 
def  div_sum(n): 
  total, i = 1, 2

  while  i * i <= n:
    if  (n % i == 0):
      total=(i+total+math.floor(n/i))
    i += 1

  return  total

def  are_equivalent(num1, num2): 
    return  div_sum(num1)==div_sum(num2); 