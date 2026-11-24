def max_product(arr):   
  n, mpis = len(arr), arr[:]
  for i in range(0, n): 
    current_prod = arr[i]
    j = i + 1
    while n > j:
      if arr[j - 1] > arr[j]: 
        break
      current_prod*=arr[j]
      if current_prod > mpis[j]:
        mpis[j]=current_prod 
      j=j + 1
  return max(mpis)