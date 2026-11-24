
def check_dict_case(dict1):
	if not dict1:
		return False
    
	all_lower = all(isinstance(key, str) and key.islower() for key in dict1.keys())
	all_upper = all(isinstance(key, str) and key.isupper() for key in dict1.keys())
    
	return all_lower or all_upper
