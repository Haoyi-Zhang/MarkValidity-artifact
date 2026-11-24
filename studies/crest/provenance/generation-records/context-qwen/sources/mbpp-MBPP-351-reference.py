
def first_Element(arr,n,k):
    count = {}
    for i in range(n):
        if arr[i] in count:
            count[arr[i]] += 1
        else:
            count[arr[i]] = 1
    for i in range(n):
        if count[arr[i]] == k:
            return arr[i]
    return -1
