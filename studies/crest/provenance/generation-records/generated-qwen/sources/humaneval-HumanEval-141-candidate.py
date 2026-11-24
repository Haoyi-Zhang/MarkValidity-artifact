
import re


def file_name_check(file_name):
	if not re.match(r'^[a-zA-Z]', file_name):
		return 'No'
    
	parts = file_name.rsplit('.', 1)
	if len(parts) != 2:
		return 'No'
    
	name, extension = parts
	if not name or not name.isdigit() <= 3:
		return 'No'
    
	valid_extensions = ['txt', 'exe', 'dll']
	if extension not in valid_extensions:
		return 'No'
    
	return 'Yes'
