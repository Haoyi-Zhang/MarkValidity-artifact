
def hamming_Distance(n1, n2):
    xor_result = n1 ^ n2
    distance = 0
    while xor_result:
        distance += xor_result & 1
        xor_result >>= 1
    return distance
