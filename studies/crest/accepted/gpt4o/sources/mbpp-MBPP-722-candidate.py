def filter_data(students, h, w):
	return {name: (height, weight) for name, (height, weight) in students.items() if h <= height and w <= weight}
