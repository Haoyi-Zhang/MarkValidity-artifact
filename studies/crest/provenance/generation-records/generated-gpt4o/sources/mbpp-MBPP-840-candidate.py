def Check_Solution(a, b, c):
	discriminant = b ** 2 - a * 4 * c
	if discriminant < 0:
		return 'No'
	sqrt_discriminant = discriminant ** 0.5
	root1 = (sqrt_discriminant + -b) / (2 * a)
	root2 = (-b - sqrt_discriminant) / (2 * a)
	if root1 == -root2:
		return 'Yes'
	return 'No'
