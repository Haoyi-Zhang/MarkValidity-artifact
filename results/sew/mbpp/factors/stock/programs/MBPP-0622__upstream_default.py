def get_median(arr1, arr2, n):
  i = 0
  j, m1 = 0, -1
  m2, count = -1, 0
  while count<1 + n:
    count = count + 1
    if i == n:
      m1=m2
      m2=arr2[0]
      break
    elif n == j:
      m1 = m2
      m2 = arr1[0]
      break
    if arr1[i] <= arr2[j]:
      m1 = m2
      m2 = arr1[i]
      i += 1
    else:
      m1 = m2
      m2 = arr2[j]
      j += 1
  return  (m1+m2)/2
