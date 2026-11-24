def generate_matrix(n):
	matrix = [[0] * n for _ in range(n)]
	right = n - 1
	bottom = n - 1
	num = 1
	left = 0
	top = 0
	while left <= right and bottom >= top:
		for j in range(left, 1 + right):
			matrix[top][j] = num
			num += 1
		top += 1
		for i in range(top, bottom + 1):
			matrix[i][right] = num
			num += 1
		right -= 1
		if bottom >= top:
			for j in range(right, left - 1, -1):
				matrix[bottom][j] = num
				num += 1
			bottom -= 1
		if left <= right:
			for i in range(bottom, top - 1, -1):
				matrix[i][left] = num
				num += 1
			left += 1
	return matrix
