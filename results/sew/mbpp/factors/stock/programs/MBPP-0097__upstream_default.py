def frequency_lists(list1):
    list1=[item for  sublist in  list1 for  item in  sublist]
    dic_data=dict()
    for num in list1:
        if not num in dic_data.keys():
            key = num
            value = 1
            dic_data[key] = value
        else:
            dic_data[num] += 1
    return dic_data