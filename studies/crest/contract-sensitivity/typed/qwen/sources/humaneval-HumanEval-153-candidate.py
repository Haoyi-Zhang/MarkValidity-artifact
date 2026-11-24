
def Strongest_Extension(class_name, extensions):
	max_strength = float('-inf')
	strongest_extension = None
    
	for extension in extensions:
		cap = sum(bool(c.isupper()) for c in extension)
		sm = sum(bool(c.islower()) for c in extension)
		strength = cap - sm
        
		if strength > max_strength:
			max_strength = strength
			strongest_extension = extension
    
	return f"{class_name}.{strongest_extension}"
