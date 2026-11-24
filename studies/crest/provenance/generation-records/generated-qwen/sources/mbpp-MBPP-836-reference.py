
def max_sub_array_sum(a, size):
    max_so_far = a[0]
    current_max = a[0]
    start = 0
    end = 0
    s = 0

    for i in range(1, size):
        if a[i] > current_max + a[i]:
            current_max = a[i]
            s = i
        else:
            current_max += a[i]

        if current_max > max_so_far:
            max_so_far = current_max
            start = s
            end = i

    return end - start + 1
