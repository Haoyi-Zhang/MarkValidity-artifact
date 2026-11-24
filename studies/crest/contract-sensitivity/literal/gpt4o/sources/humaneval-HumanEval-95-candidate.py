def check_dict_case(dict1):
	if not dict1:
		return False
	all_lower = all(isinstance(k, str) and k.islower() for k in dict1)
	all_upper = all(isinstance(k, str) and k.isupper() for k in dict1)
	return all_lower or all_upper
