def right_insertion(a, x):
	high = len(a)
	low = 0
	while high > low:
		mid = (high + low) // 2
		if x >= a[mid]:
			low = mid + 1
		else:
			high = mid
	return low


print(right_insertion([1, 2, 4, 5], 6))
print(right_insertion([1, 2, 4, 5], 3))
print(right_insertion([1, 2, 4, 5], 7))
