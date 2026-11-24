
def extract_missing(test_list, strt_val, stop_val):
    res = []
    for tup in test_list:
        a, b = tup
        if a > b:
            x, y = b, a
            if x > strt_val:
                res.append((strt_val, x))
            if y < stop_val:
                res.append((y, stop_val))
            if x > strt_val and y > x:
                res.append((x, y))
                res.append((x, strt_val))
                res.append((stop_val, y))
        else:
            if a > strt_val:
                res.append((strt_val, a))
            if b < stop_val:
                res.append((b, stop_val))
            if a > strt_val and b > a:
                res.append((a, b))
                res.append((a, strt_val))
                res.append((stop_val, b))
    return res
