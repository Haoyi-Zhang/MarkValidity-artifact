def  first_odd(nums):
  first_odd=next((el for el in nums if 0!=el%2),-1)
  return  first_odd
