
def find_Element(arr, ranges, rotations, index):
    for i in range(rotations):
        left = ranges[i][0]
        right = ranges[i][1]
        arr[left:right+1] = reversed(arr[left:right+1])
    return arr[index]
