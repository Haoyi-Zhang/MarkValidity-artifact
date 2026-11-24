
if n == 0:
    return 0
elif n == 1:
    return arr[0]
elif n == 2:
    return max(arr[0], arr[1])
else:
    incl = max(arr[0], arr[1] + arr[2])
    excl = arr[0]
    for i in range(3, n):
        new_excl = max(excl, incl)
        incl = excl + arr[i]
        excl = new_excl
    return max(excl, incl)
