
def filter_data(students, h, w):
    return {name: data for name, data in students.items() if data[0] > h and data[1] > w}
