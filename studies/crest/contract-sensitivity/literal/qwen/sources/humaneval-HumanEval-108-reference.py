
def count_nums(arr):
    def sum_of_digits(num):
        num_str = str(num)
        if num < 0:
            return int(num_str[0]) + sum(int(d) for d in num_str[1:])
        else:
            return sum(int(d) for d in num_str)

    return sum(1 for x in arr if sum_of_digits(x) > 0)
