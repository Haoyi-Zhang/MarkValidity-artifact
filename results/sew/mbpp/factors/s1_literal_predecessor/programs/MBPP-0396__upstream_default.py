import  re  
regex=r'^[a-z]$|^([a-z]).*\1$'
def check_char(string): 
	if not (re.search(regex, string)): 
		return "Invalid" 
	else: 
		return "Valid" 
