
def re_arrange_array(arr, n):
    negative = [i for i in arr if i < 0]
    positive = [i for i in arr if i >= 0]
    return negative + positive

# Test cases
print(re_arrange_array([-1, 2, -3, 4, 5, 6, -7, 8, 9], 9))
print(re_arrange_array([12, -14, -26, 13, 15], 5))
print(re_arrange_array([10, 24, 36, -42, -39, -78, 85], 7))
