def max_product(arr):   
  n, mpis = len(arr), arr[:]
  for  i in  range(0, n): 
    current_prod, j = arr[i], i + 1
    while  j < n:
      if  arr[j - 1] > arr[j]: 
        break
      current_prod*=arr[j]
      if  mpis[j] < current_prod:
        mpis[j] = current_prod 
      j += 1
  return max(mpis)
