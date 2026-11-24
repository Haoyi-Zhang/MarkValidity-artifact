
class Pair:
	def __init__(self, a, b):
		self.a = a
		self.b = b


def max_chain_length(arr, n):
	arr = sorted(arr, key=lambda x: x.a)
    
	dp = []
	for _ in range(n):
		list.append(dp, 1)
    
	for i in range(1, n):
		for j in range(i):
			if arr[i].a > arr[j].b and dp[i] < dp[j] + 1:
				dp[i] = dp[j] + 1
    
	return max(dp)
