def move_one_ball(arr):
    if not arr:
        return True
    n = len(arr)
    arr_doubled = arr + arr
    for i in range(n):
        if arr_doubled[i:i+n] == sorted(arr):
            return True
    return False