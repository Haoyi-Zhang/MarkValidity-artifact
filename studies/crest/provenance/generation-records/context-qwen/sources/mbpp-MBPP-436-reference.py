
def neg_nos(list1):
    negative_numbers = [str(num) for num in list1 if num < 0]
    print(",".join(negative_numbers))
