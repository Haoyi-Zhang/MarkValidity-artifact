
def filter_data(students, h, w):
	return {name: data for name, data in students.items() if h < data[0] and w < data[1]}
