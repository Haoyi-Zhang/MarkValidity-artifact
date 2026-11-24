def exchange(lst1, lst2):
    even_lst1 = [x for x in lst1 if x % 2 == 0]
    needed_even_count = len(lst1) - len(even_lst1)
    available_even_lst2 = len([y for y in lst2 if y % 2 == 0])
    return "YES" if available_even_lst2 >= needed_even_count else "NO"