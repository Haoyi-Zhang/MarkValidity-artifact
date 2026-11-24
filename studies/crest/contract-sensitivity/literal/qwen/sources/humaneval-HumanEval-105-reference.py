
def by_length(arr):
    digit_names = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    filtered_arr = [x for x in arr if 1 <= x <= 9]
    sorted_reversed_arr = sorted(filtered_arr, reverse=True)
    named_arr = [digit_names[x - 1] for x in sorted_reversed_arr]
    return named_arr
