
def convert_list_dictionary(l1, l2, l3):
    return [{l1[i]: {l2[i]: l3[i]}} for i in range(len(l1))]
