
def get_max_sum(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 2:
        return n
    max_sum = max((get_max_sum(n//2, memo) + get_max_sum(n//3, memo) + get_max_sum(n//4, memo) + get_max_sum(n//5, memo)), n)
    memo[n] = max_sum
    return max_sum
