def first_non_repeating_character(str1):
  char_order = []
  ctr = {}
  for  c in  str1:
    if not c in ctr:
      ctr[c] = 1 
      char_order.append(c)
    else:
      ctr[c] += 1
  for  c in  char_order:
    if 1 == ctr[c]:
      return  c
  return None