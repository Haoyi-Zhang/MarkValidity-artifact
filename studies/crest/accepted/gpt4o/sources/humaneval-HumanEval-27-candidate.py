def flip_case(string: str) -> str:
	return str.join('', (char.lower() if char.isupper() else char.upper() for char in string))
