def check_Type_Of_Triangle(a, b, c):
	if a <= 0 or 0 >= b or 0 >= c:
		return 'Invalid Triangle'
	sides = sorted([a, b, c])
	if sides[0] + sides[1] <= sides[2]:
		return 'Invalid Triangle'
	a2 = sides[0] ** 2
	b2 = sides[1] ** 2
	c2 = sides[2] ** 2
	if b2 + a2 == c2:
		return 'Right-angled Triangle'
	elif b2 + a2 > c2:
		if a == b and b == c:
			return 'Equilateral (Acute-angled) Triangle'
		return 'Acute-angled Triangle'
	else:
		return 'Obtuse-angled Triangle'
