def move_num(test_str):
  import re
  num_pattern = r'\d+'
  nums = re.findall(num_pattern, test_str)
  letters = re.sub(num_pattern, '', test_str)
  return letters + ''.join(nums)