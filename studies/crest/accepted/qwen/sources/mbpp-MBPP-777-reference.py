
def find_Sum(arr,n):
    from collections import Counter
    count = Counter(arr)
    return sum([x for x in arr if count[x] == 1])
