def find_Average_Of_Cube(n):  
    sum=0
    for i in range(1, 1 + n): 
        sum+=i*i*i  
    return round(sum / n, 6) 