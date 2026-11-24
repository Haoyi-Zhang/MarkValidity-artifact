
def count_Substring_With_Equal_Ends(s):
    n = len(s)
    count = 0
    for i in range(n):
        count += (n - i)
    return count
