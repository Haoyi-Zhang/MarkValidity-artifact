def remove_splchar(text):
	return str.join('', (char for char in text if char.isalnum()))
