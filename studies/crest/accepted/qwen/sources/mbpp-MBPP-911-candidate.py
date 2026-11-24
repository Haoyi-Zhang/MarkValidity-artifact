
import heapq


def maximum_product(nums):
	if len(nums) < 3:
		raise ValueError("Array must contain at least three elements")
    
	# Find the three largest numbers
	largest = heapq.nlargest(3, nums)
    
	# Calculate the product of the three largest numbers
	return largest[0] * largest[1] * largest[2]
