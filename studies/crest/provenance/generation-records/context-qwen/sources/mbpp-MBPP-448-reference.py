
def cal_sum(n):
    if n < 3:
        return n
    perrin = [3, 0, 2]
    for i in range(3, n):
        perrin.append(perrin[i-2] + perrin[i-3])
    return sum(perrin)
