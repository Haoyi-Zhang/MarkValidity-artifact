def match_parens(lst):
    left_count1 = lst[0].count('(')
    right_count1 = lst[0].count(')')
    left_count2 = lst[1].count('(')
    right_count2 = lst[1].count(')')
    if left_count1 + left_count2 == right_count1 + right_count2:
        return 'Yes'
    return 'No'