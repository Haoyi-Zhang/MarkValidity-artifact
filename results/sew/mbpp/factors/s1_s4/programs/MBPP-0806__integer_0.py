def  max_run_uppercase(test_str):
  cnt = res = 0
  for idx in range(len(test_str)):
    if test_str[idx].isupper():
      cnt += 1
    else:
      res = cnt
      cnt = 0
  if test_str[len(test_str) - 1].isupper():
    res=cnt
  return  (res)