def  average_tuple(nums):
    result=[sum(x, 0)/len(x) for x in zip(*nums)]
    return  result
