
def by_length(arr):
	filtered_arr = [x for x in arr if 1 <= x and x <= 9]
	sorted_reversed_arr = sorted(filtered_arr, reverse=True)
	digit_names = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
	return [digit_names[x - 1] for x in sorted_reversed_arr]
