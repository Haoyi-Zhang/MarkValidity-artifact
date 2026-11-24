
def largest_neg(list1):
    neg_numbers = [num for num in list1 if num < 0]
    return max(neg_numbers) if neg_numbers else None
