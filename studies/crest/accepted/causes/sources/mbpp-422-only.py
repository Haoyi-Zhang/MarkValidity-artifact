def find_Average_Of_Cube(n):  
    sum = sum((i * i * i for i in range(1, n + 1)))
    return round(sum / n, 6) 