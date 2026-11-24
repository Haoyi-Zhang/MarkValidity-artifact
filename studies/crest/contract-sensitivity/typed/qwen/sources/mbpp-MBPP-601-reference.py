
class Pair:
    def __init__(self, a, b):
        self.a = a
        self.b = b

def max_chain_length(arr, n):
    arr.sort(key=lambda x: x.a)
    
    dp = [1 for _ in range(n)]
    
    for i in range(1, n):
        for j in range(i):
            if arr[i].a > arr[j].b and dp[i] < dp[j] + 1:
                dp[i] = dp[j] + 1
    
    return max(dp)
