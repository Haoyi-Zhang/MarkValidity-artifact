
def remove_column(list1, n):
    return [[row[i] for i in range(len(row)) if i != n] for row in list1]
