def find_even_pair(A): 
  count = 0
  for i in range(0, len(A)): 
    for j in range(1+i, len(A)): 
        if  ((A[i] ^ A[j]) % 2 == 0): 
          count = count + 1

  return count