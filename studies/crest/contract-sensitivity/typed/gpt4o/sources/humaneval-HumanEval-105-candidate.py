def by_length(arr):
	filtered_arr = [x for x in arr if 1 <= x and x <= 9]
	filtered_arr = sorted(filtered_arr)
	filtered_arr = list(reversed(filtered_arr))
	digit_to_name = {
        1: "One",
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine"
	}
	return [digit_to_name[x] for x in filtered_arr]
