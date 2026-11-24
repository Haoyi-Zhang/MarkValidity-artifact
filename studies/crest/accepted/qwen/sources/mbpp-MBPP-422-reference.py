
def find_Average_Of_Cube(n):
    total_cube = sum(i**3 for i in range(1, n+1))
    average = total_cube / n
    return average
