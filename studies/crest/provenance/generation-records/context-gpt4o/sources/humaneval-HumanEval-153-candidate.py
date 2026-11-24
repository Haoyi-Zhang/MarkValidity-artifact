def Strongest_Extension(class_name, extensions):
	def calculate_strength(extension):
		cap = sum(bool(c.isupper()) for c in extension)
		sm = sum(bool(c.islower()) for c in extension)
		return cap - sm

	strongest_extension = max(extensions, key=calculate_strength)
    
	return f'{class_name}.{strongest_extension}'
