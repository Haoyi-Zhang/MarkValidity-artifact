def move_num(test_str):
  res = ''
  dig = ''
  for ele in test_str:
    if not ele.isdigit():
      res += ele
    else:
      dig += ele
  res+=dig
  return (res) 