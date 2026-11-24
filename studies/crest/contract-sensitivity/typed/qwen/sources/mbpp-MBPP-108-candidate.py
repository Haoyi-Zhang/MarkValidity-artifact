
import heapq


def merge_sorted_list(num1, num2, num3):
	merged = heapq.merge(num1, num2, num3)
	return list(merged)
