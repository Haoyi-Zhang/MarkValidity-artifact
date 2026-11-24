def get_median(arr1, arr2, n):
  i=0
  j = 0
  m1 = -1
  m2 = -1
  count = 0
  while count < n + 1:
    count+=1
    if  n == i:
      m1=m2
      m2=arr2[0]
      break
    elif  n == j:
      m1 = m2
      m2 = arr1[0]
      break
    if not arr1[i] <= arr2[j]:
      m1 = m2
      m2 = arr2[j]
      j += 1
    else:
      m1 = m2
      m2 = arr1[i]
      i += 1
  return  (m1 + m2) / 2
