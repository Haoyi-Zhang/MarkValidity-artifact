
def find_longest_conseq_subseq(arr, n):
	arr = list(set(arr))
	arr = sorted(arr)
	longest_streak = 0
	current_streak = 1
    
	for i in range(1, len(arr)):
		if arr[i] == 1 + arr[i - 1]:
			current_streak += 1
		else:
			longest_streak = max(longest_streak, current_streak)
			current_streak = 1
    
	return max(longest_streak, current_streak)
