
def issort_list(list1):
    return all(list1[i] <= list1[i + 1] for i in range(len(list1) - 1))
