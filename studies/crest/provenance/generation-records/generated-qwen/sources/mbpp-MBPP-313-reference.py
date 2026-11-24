
def pos_nos(list1):
    positive_numbers = [num for num in list1 if num > 0]
    print(",".join(map(str, positive_numbers)))
