
def check_subset_list(list1, list2):
    for sublist in list2:
        if not set(sublist).issubset(set(list1)):
            return False
    return True
