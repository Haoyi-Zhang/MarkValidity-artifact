
def Total_Hamming_Distance(n):
    total_distance = 0
    for i in range(n + 1):
        for j in range(i + 1, n + 1):
            total_distance += bin(i ^ j).count('1')
    return total_distance
