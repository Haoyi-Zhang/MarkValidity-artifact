def prime_num(num):
  if num >=1:
   for i in range(2, num//2):
     if not (num % i) == 0:
                return True
     else:
                return False
  else:
          return False