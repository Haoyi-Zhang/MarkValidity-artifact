def  count_occurance(s):
  count=0
  for  i in  range(0, len(s) - 2):
    if  (s[i]=='s' and  s[i+1]=='t' and  s[i+2]=='d'):
      count=1 + count
  return count
