
def find_First_Missing(array, start, end):
    for i in range(start, end + 1):
        if i not in array:
            return i
    return end + 1
