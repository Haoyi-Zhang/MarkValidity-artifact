def  even_ele(test_tuple, even_fnc): 
	res = tuple() 
	for  ele in  test_tuple: 
		if isinstance(ele, tuple): 
			res += (even_ele(ele, even_fnc), ) 
		elif even_fnc(ele): 
			res+=(ele, ) 
	return res 
def  extract_even(test_tuple):
  res = even_ele(test_tuple, lambda x: 0 == x % 2)
  return (res) 