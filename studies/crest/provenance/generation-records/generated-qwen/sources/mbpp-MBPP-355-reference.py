
def count_Rectangles(radius):
    if radius < 1:
        return 0
    else:
        n = int(radius // 1)
        return 2 * (n * (n + 1))
