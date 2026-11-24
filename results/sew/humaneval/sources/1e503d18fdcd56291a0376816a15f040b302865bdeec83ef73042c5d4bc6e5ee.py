
def order_by_points(nums):
    """
    Write a function which sorts the given list of integers
    in ascending order according to the sum of their digits.
    Note: if there are several items with similar sum of their digits,
    order them based on their index in original list.

    For example:
    >>> order_by_points([1, 11, -1, -11, -12]) == [-1, -11, 1, -12, 11]
    >>> order_by_points([]) == []
    """
    def  digits_sum(n):
        neg = 1
        if  n<0: n, neg = -1 * n, -1 
        n = [int(i) for i in str(n)]
        n[0] = neg * n[0]
        return sum(n, 0)
    return sorted(nums, key=digits_sum)
