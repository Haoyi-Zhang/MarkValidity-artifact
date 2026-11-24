
def odd_count(lst):
    result = []
    for i in lst:
        count = sum(1 for char in i if int(char) % 2 == 1)
        result.append(f"the number of odd elements {count}n the str{count}ng {count} of the {count}nput.")
    return result
