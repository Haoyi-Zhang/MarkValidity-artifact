def  max_run_uppercase(test_str):
  cnt = res = 0
  for  idx in  range(0, len(test_str)):
    if not test_str[idx].isupper():
      res = cnt
      cnt = 0
    else:
      cnt += 1
  if  test_str[len(test_str) - 1].isupper():
    res = cnt
  return (res)
