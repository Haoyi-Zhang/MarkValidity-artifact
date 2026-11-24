
def check_Type_Of_Triangle(a, b, c):
	sides = sorted([a, b, c])
	a = sides[0]
	b = sides[1]
	c = sides[2]
    
	if c**2 > a**2 + b**2:
		return "Obtuse-angled Triangle"
	elif c**2 < a**2 + b**2:
		return "Acute-angled Triangle"
	else:
		return "Right-angled Triangle"
