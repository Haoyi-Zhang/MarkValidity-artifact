
def sub_lists(my_list):
    subs = [[]]
    for i in range(len(my_list)):
        n = len(subs)
        for j in range(n):
            subs.append(subs[j] + [my_list[i]])
    return subs
