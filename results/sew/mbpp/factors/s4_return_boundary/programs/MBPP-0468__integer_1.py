def  max_product(arr):   
  n = len(arr)
  mpis = arr[:]
  for  i in  range(0, n): 
    current_prod, j = arr[i], i + 1
    while n > j:
      if  arr[j - 1] > arr[j]: 
        break
      current_prod *= arr[j]
      if  current_prod > mpis[j]:
        mpis[j] = current_prod 
      j = j + 1
  return  max(mpis)
